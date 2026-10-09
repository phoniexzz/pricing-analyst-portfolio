param([string]$ProjectRoot = (Split-Path $PSScriptRoot -Parent))
$ErrorActionPreference='Stop'
$taskLibrary=Join-Path $PSScriptRoot '.powerbi_tools\tom\lib\netcoreapp3.0'
if(-not (Test-Path -LiteralPath (Join-Path $taskLibrary 'Microsoft.AnalysisServices.Tabular.dll'))) {
    throw 'Microsoft Analysis Services TOM 19.84.1 is required. See powerbi/SETUP.md for the optional offline model-parser check.'
}
Add-Type -Path (Join-Path $taskLibrary 'Microsoft.AnalysisServices.Core.dll')
Add-Type -Path (Join-Path $taskLibrary 'Microsoft.AnalysisServices.Tabular.dll')
$taskModelPath=Join-Path $ProjectRoot 'powerbi\Northstar.SemanticModel\definition'
$taskDatabase=[Microsoft.AnalysisServices.Tabular.TmdlSerializer]::DeserializeDatabaseFromFolder($taskModelPath)
$taskModel=$taskDatabase.Model
$taskSchema=Get-Content -LiteralPath (Join-Path $ProjectRoot 'powerbi\model_schema.json') -Raw | ConvertFrom-Json -AsHashtable
if($taskModel.Tables.Count -ne ($taskSchema.tables.Count+1)) {throw 'Unexpected/orphan model table'}
foreach($taskRelation in $taskModel.Relationships){
 if($taskRelation.CrossFilteringBehavior.ToString() -ne 'OneDirection'){throw 'Bidirectional relationship'}
 if(-not $taskRelation.ToTable.Name.StartsWith('Dim')){throw 'Fact-to-fact relationship'}
}
foreach($taskTable in $taskModel.Tables){
 if($taskTable.Name -eq 'CommercialMeasures'){continue}
 foreach($taskColumn in $taskTable.Columns){
  if(-not $taskSchema.tables[$taskTable.Name].columns.ContainsKey($taskColumn.Name)){throw 'Unknown model column'}
 }
}
$taskCount=($taskModel.Tables | ForEach-Object {$_.Measures.Count} | Measure-Object -Sum).Sum
$taskResult=@{status='TMDL parsed by Microsoft TOM; DAX and M execution remain pending';tom_package='Microsoft.AnalysisServices.NetCore.retail.amd64 19.84.1';tables=$taskModel.Tables.Count;relationships=$taskModel.Relationships.Count;measures=$taskCount;compatibility_level=$taskDatabase.CompatibilityLevel;native_powerbi='pending'}
$taskResult | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'powerbi_tmdl_verification.json') -Encoding utf8NoBOM
$taskResult | ConvertTo-Json
