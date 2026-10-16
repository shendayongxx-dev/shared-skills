[CmdletBinding()]
param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$zh = Join-Path $repo "skills/zh/ecommerce-poster-design"
$en = Join-Path $repo "skills/en/ecommerce-poster-design"

function Invoke-PythonCheck {
    param([Parameter(Mandatory)][string[]]$Arguments)
    & $Python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Validation failed: $Python $($Arguments -join ' ')"
    }
}

Invoke-PythonCheck @((Join-Path $PSScriptRoot "validate_english_release.py"))
Invoke-PythonCheck @((Join-Path $PSScriptRoot "validate_edition_equivalence.py"))

foreach ($root in @($zh, $en)) {
    Push-Location $root
    try {
        Invoke-PythonCheck @((Join-Path $root "scripts/validate_classification.py"), (Join-Path $root "assets/classification"))
        Invoke-PythonCheck @((Join-Path $root "scripts/test_canvas_normalization.py"))
        Invoke-PythonCheck @((Join-Path $root "scripts/test_consumer_routing.py"))
        Invoke-PythonCheck @((Join-Path $root "scripts/test_aesthetic_integration.py"))
        Invoke-PythonCheck @((Join-Path $root "scripts/test_final_quality_routing.py"))
        Invoke-PythonCheck @((Join-Path $root "scripts/test_logo_verification.py"))
        Invoke-PythonCheck @((Join-Path $root "scripts/validate_consumer_integration.py"))
        Invoke-PythonCheck @((Join-Path $root "scripts/validate_aesthetic_integration.py"))
        Invoke-PythonCheck @((Join-Path $root "scripts/validate_final_quality_integration.py"))
        Invoke-PythonCheck @((Join-Path $root "scripts/validate_logo_pipeline.py"))
        Invoke-PythonCheck @((Join-Path $root "modules/aesthetic-agent/tests/test_score_evaluation.py"))
        Invoke-PythonCheck @((Join-Path $root "modules/consumer-agent/scripts/run_evals.py"))
    }
    finally {
        Pop-Location
    }
}

Write-Output "PASS: Chinese/English instruction-edition rc.7 validation completed"
