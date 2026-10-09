param([int]$Port=50551)
$ErrorActionPreference='Stop'
Add-Type -Path (Join-Path $PSScriptRoot '.powerbi_tools/tom/lib/netcoreapp3.0/Microsoft.AnalysisServices.Core.dll')
Add-Type -Path (Join-Path $PSScriptRoot '.powerbi_tools/tom/lib/netcoreapp3.0/Microsoft.AnalysisServices.Tabular.dll')
Add-Type -Path (Join-Path $PSScriptRoot '.powerbi_tools/adomd/lib/netcoreapp3.0/Microsoft.AnalysisServices.AdomdClient.dll')
$taskServer=[Microsoft.AnalysisServices.Tabular.Server]::new()
$taskServer.Connect("Data Source=localhost:$Port")
$taskDb=@($taskServer.Databases | Where-Object {@($_.Model.Tables | Where-Object {$_.Name -eq 'CommercialMeasures' -and $_.Measures.Count -eq 296}).Count -eq 1})
if($taskDb.Count -ne 1){throw 'Expected exactly one native Northstar model'}
$taskConnection=[Microsoft.AnalysisServices.AdomdClient.AdomdConnection]::new("Data Source=localhost:$Port;Initial Catalog=$($taskDb[0].ID)")
$taskConnection.Open()
function Invoke-TaskDax([string]$Query){
 $taskCommand=$taskConnection.CreateCommand();$taskCommand.CommandText=$Query
 $taskReader=$taskCommand.ExecuteReader();$taskRows=[System.Collections.Generic.List[object]]::new()
 while($taskReader.Read()){
  $taskRow=[ordered]@{}
  for($taskI=0;$taskI -lt $taskReader.FieldCount;$taskI++){
   $taskRow[$taskReader.GetName($taskI)]=if($taskReader.IsDBNull($taskI)){$null}else{$taskReader.GetValue($taskI)}
  }
  $taskRows.Add($taskRow)
 }
 $taskReader.Close();return ,($taskRows.ToArray())
}
$taskRoot=Split-Path $PSScriptRoot -Parent
$taskText=Get-Content -LiteralPath (Join-Path $taskRoot 'powerbi/DAX_checks.dax') -Raw
$taskText=[regex]::Replace($taskText,'(?m)^//.*$','')
$taskQueries=[regex]::Split($taskText,'(?m)(?=^EVALUATE)') | Where-Object {$_.Trim().StartsWith('EVALUATE')}
$taskResults=@();$taskIndex=0
foreach($taskQuery in $taskQueries){$taskIndex++;$taskResults+=@{check=$taskIndex;query=$taskQuery.Trim();rows=(Invoke-TaskDax $taskQuery)}}
$taskErrors=@($taskDb[0].Model.Tables | ForEach-Object {$_.Measures} | Where-Object {$_.State.ToString() -eq 'SemanticError' -or $_.ErrorMessage} | ForEach-Object {@{measure=$_.Name;state=$_.State.ToString();error=$_.ErrorMessage}})
$taskMeasureNames=@($taskDb[0].Model.Tables | Where-Object {$_.Name -eq 'CommercialMeasures'} | ForEach-Object {$_.Measures} | ForEach-Object {$_.Name})
$taskAllMeasures='EVALUATE CALCULATETABLE(ROW(' + (($taskMeasureNames | ForEach-Object {'"'+$_.Replace('"','""')+'",['+$_.Replace(']',']]')+']'}) -join ',') + '),DimHistoryMonth[year]=2025,DimCase[case]="Base",DimPrice[price_increment]=1,DimPolicy[variant]="base",DimSimulation[simulation]="Main",DimPopulation[population]="First repricing",DimCheckpoint[checkpoint_months]=6,DimGym[gym_id]="NF001")'
$taskEvaluatedMeasures=Invoke-TaskDax $taskAllMeasures
if($null -eq $taskResults[0].rows[0]['[Revenue 2025]'] -or [Math]::Abs($taskResults[0].rows[0]['[Revenue 2025]']-107006933.85) -gt 0.01){throw 'Native refresh incomplete or revenue anchor mismatch'}
if($taskResults[0].rows[0]['[December members]'] -ne 396311){throw 'Native member anchor mismatch'}
if([Math]::Abs($taskResults[1].rows[0]['[Base portfolio uplift]']-148618.48020484) -gt 0.01){throw 'Native portfolio anchor mismatch'}
if($null -ne $taskResults[4].rows[0]['[Multiple-case/option refusal]'] -or $null -ne $taskResults[4].rows[0]['[Unsupported two-gym interval]']){throw 'Unsupported aggregation/range not suppressed'}
if($taskResults[5].rows[0]['[Main primary six-month decision]'] -ne 'EXTEND TEST' -or $taskResults[6].rows[0]['[Main primary twelve-month decision]'] -ne 'STOP'){throw 'Saved experiment decisions changed'}
$taskResult=@{executed_at=(Get-Date -Format o);engine='Power BI Desktop local Analysis Services';port=$Port;catalog=$taskDb[0].ID;checks=$taskResults;all_measure_execution=$taskEvaluatedMeasures;measure_errors=$taskErrors;measures=$taskMeasureNames.Count}
$taskExtraText=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'powerbi_native_extra.dax') -Raw
$taskExtraText=[regex]::Replace($taskExtraText,'(?m)^//.*$','')
$taskExtra=@();$taskExtraIndex=0
foreach($taskQuery in ([regex]::Split($taskExtraText,'(?m)(?=^EVALUATE)') | Where-Object {$_.Trim().StartsWith('EVALUATE')})){$taskExtraIndex++;$taskExtra+=@{check=$taskExtraIndex;rows=(Invoke-TaskDax $taskQuery)}}
$taskResult['additional_checks']=$taskExtra
$taskResult['table_counts']=@($taskDb[0].Model.Tables | Where-Object {$_.Name -ne 'CommercialMeasures'} | ForEach-Object {@{table=$_.Name;rows=(Invoke-TaskDax ('EVALUATE ROW("Rows",COUNTROWS('+$_.Name+'))'))}})
$taskResult | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'powerbi_native_dax_results.json') -Encoding utf8NoBOM
$taskConnection.Close();$taskServer.Disconnect()
$taskResults | ForEach-Object {"Check $($_.check): " + ($_.rows | ConvertTo-Json -Depth 5 -Compress)}
if($taskErrors.Count){throw 'Native measure errors found'}
