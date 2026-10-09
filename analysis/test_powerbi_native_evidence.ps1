param([int]$Port,[ValidateSet('Stale','Restore')] [string]$Mode)
$ErrorActionPreference='Stop'
Add-Type -Path (Join-Path $PSScriptRoot '.powerbi_tools/tom/lib/netcoreapp3.0/Microsoft.AnalysisServices.Core.dll')
Add-Type -Path (Join-Path $PSScriptRoot '.powerbi_tools/tom/lib/netcoreapp3.0/Microsoft.AnalysisServices.Tabular.dll')
$taskServer=[Microsoft.AnalysisServices.Tabular.Server]::new();$taskServer.Connect("Data Source=localhost:$Port")
$taskDb=@($taskServer.Databases | Where-Object {@($_.Model.Tables | Where-Object {$_.Name -eq 'CommercialMeasures'}).Count -eq 1})
if($taskDb.Count -ne 1){throw 'Expected one Northstar model'}
$taskTable=$taskDb[0].Model.Tables | Where-Object {$_.Name -eq 'EvidenceStatus'}
$taskPartition=$taskTable.Partitions[0]
$taskBackup=Join-Path $PSScriptRoot '.powerbi_native/evidence_partition.json'
if($Mode -eq 'Stale'){
 @{expression=$taskPartition.Source.Expression;catalog=$taskDb[0].ID} | ConvertTo-Json | Set-Content -LiteralPath $taskBackup -Encoding utf8NoBOM
 $taskRoot=Split-Path $PSScriptRoot -Parent
 $taskStatus=Import-Csv -LiteralPath (Join-Path $taskRoot 'powerbi/model_data/EvidenceStatus.csv')
 $taskStatus.forward_current='False';$taskStatus.experiment_current='False';$taskStatus.evidence_message='STALE verification fixture — authoritative forward/experiment conclusions suppressed'
 $taskFixture=Join-Path $PSScriptRoot '.powerbi_native/stale_EvidenceStatus.csv'
 $taskStatus | Export-Csv -LiteralPath $taskFixture -NoTypeInformation -Encoding utf8NoBOM
 $taskPartition.Source.Expression=$taskPartition.Source.Expression.Replace('File.Contents(SourceRoot & "/EvidenceStatus.csv")','File.Contents("'+$taskFixture.Replace('\','/')+'")')
 if($taskPartition.Source.Expression -notlike '*stale_EvidenceStatus.csv*'){throw 'Fixture query not set'}
}else{
 $taskSaved=Get-Content -LiteralPath $taskBackup -Raw | ConvertFrom-Json
 if($taskSaved.catalog -ne $taskDb[0].ID){throw 'Restore must target the same native model'}
 $taskPartition.Source.Expression=$taskSaved.expression
}
$taskTable.RequestRefresh([Microsoft.AnalysisServices.Tabular.RefreshType]::Full)
$taskDb[0].Model.SaveChanges()
Add-Type -Path (Join-Path $PSScriptRoot '.powerbi_tools/adomd/lib/netcoreapp3.0/Microsoft.AnalysisServices.AdomdClient.dll')
$taskConn=[Microsoft.AnalysisServices.AdomdClient.AdomdConnection]::new("Data Source=localhost:$Port;Initial Catalog=$($taskDb[0].ID)");$taskConn.Open()
$taskCommand=$taskConn.CreateCommand();$taskCommand.CommandText='EVALUATE CALCULATETABLE(ROW("Forward current",[Forward Evidence Current],"Experiment current",[Experiment Evidence Current],"Scenario",[Scenario Revenue],"Recommendation",[Saved Recommendation],"Decision",[Experiment Saved Decision]),DimCase[case]="Base",DimPrice[price_increment]=1,DimGym[gym_id]="NF001",DimSimulation[simulation]="Main",DimPopulation[population]="First repricing",DimCheckpoint[checkpoint_months]=6)'
$taskReader=$taskCommand.ExecuteReader();$taskReader.Read() | Out-Null;$taskProof=[ordered]@{}
for($taskI=0;$taskI -lt $taskReader.FieldCount;$taskI++){$taskProof[$taskReader.GetName($taskI)]=if($taskReader.IsDBNull($taskI)){$null}else{$taskReader.GetValue($taskI)}}
$taskReader.Close();$taskConn.Close()
$taskProof | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot "powerbi_native_evidence_$Mode.json") -Encoding utf8NoBOM
if($Mode -eq 'Stale' -and ($taskProof['[Forward current]'] -or $taskProof['[Experiment current]'] -or $null -ne $taskProof['[Scenario]'])){throw 'Stale suppression failed'}
if($Mode -eq 'Restore' -and (-not $taskProof['[Forward current]'] -or -not $taskProof['[Experiment current]'] -or $null -eq $taskProof['[Scenario]'])){throw 'Evidence restoration failed'}
$taskServer.Disconnect()
Write-Output "Native evidence fixture: $Mode. Original snapshot CSV unchanged. Restore before any native save."
