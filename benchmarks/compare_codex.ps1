$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$dataset = Join-Path $PSScriptRoot 'vendor/polyglot-benchmark'
$results = Join-Path $PSScriptRoot 'results'
$env:CODEX_HOME = 'C:/Users/deanl/.codex'
$codexPath = (Get-Command codex).Source
$rows = @()
foreach ($name in @('affine-cipher', 'beer-song', 'book-store')) {
    $source = Join-Path $dataset "python/exercises/practice/$name"
    $work = Join-Path $PSScriptRoot "work/codex-comparison-reviewed/$name"
    if (Test-Path -LiteralPath $work) { throw "Refusing to overwrite $work" }
    New-Item -ItemType Directory -Path $work -Force | Out-Null
    Get-ChildItem -LiteralPath $source -Filter '*.py' | Copy-Item -Destination $work
    Copy-Item -LiteralPath (Join-Path $source '.docs') -Destination $work -Recurse
    $files = (Get-ChildItem -LiteralPath $work -Filter '*.py' | Where-Object Name -NotLike '*_test.py').Name -join ', '
    $instructions = (Get-ChildItem -LiteralPath (Join-Path $work '.docs') -Filter '*.md' | Sort-Object Name | ForEach-Object { Get-Content -LiteralPath $_.FullName -Raw }) -join "`n`n"
    $prompt = "Complete this Python Exercism exercise: $name.`nImplement the solution in $files. Read existing files before editing. Do not modify tests or metadata. Run the existing tests to verify your solution.`n`n$instructions"
    $info = New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName = $codexPath
    $info.Arguments = 'exec --json --ignore-user-config --ephemeral --skip-git-repo-check --approve-for-me -m gpt-6-luna -C "' + $work + '" -'
    $info.WorkingDirectory = $work
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardInput = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $info
    $timer = [Diagnostics.Stopwatch]::StartNew()
    [void]$process.Start()
    $stdout = $process.StandardOutput.ReadToEndAsync()
    $stderr = $process.StandardError.ReadToEndAsync()
    $process.StandardInput.Write($prompt)
    $process.StandardInput.Close()
    $timedOut = -not $process.WaitForExit(180000)
    if ($timedOut) { $process.Kill(); $process.WaitForExit() }
    $agentSeconds = $timer.Elapsed.TotalSeconds
    $eventsText = $stdout.GetAwaiter().GetResult()
    $errorText = $stderr.GetAwaiter().GetResult()
    [IO.File]::WriteAllText((Join-Path $results "codex-$name.jsonl"), $eventsText)
    [IO.File]::WriteAllText((Join-Path $results "codex-$name.stderr.txt"), $errorText)
    $events = @($eventsText -split "`n" | Where-Object { $_.Trim() } | ForEach-Object { try { $_ | ConvertFrom-Json } catch {} })
    $usage = @($events | Where-Object type -EQ 'turn.completed')
    $inputTokens = ($usage | ForEach-Object { $_.usage.input_tokens } | Measure-Object -Sum).Sum
    $outputTokens = ($usage | ForEach-Object { $_.usage.output_tokens } | Measure-Object -Sum).Sum
    $cachedTokens = ($usage | ForEach-Object { $_.usage.cached_input_tokens } | Measure-Object -Sum).Sum
    Get-ChildItem -LiteralPath $source -Filter '*_test.py' | Copy-Item -Destination $work
    $linuxWork = '/mnt/c/' + $work.Substring(3).Replace('\', '/')
    $testOutput = & wsl.exe --exec /mnt/c/Users/deanl/Documents/harness/.venv/bin/python /mnt/c/Users/deanl/Documents/harness/benchmarks/grade_task.py $linuxWork | Out-String
    $passed = $LASTEXITCODE -eq 0
    $row = [ordered]@{task=$name; input_tokens=$inputTokens; cached_input_tokens=$cachedTokens; output_tokens=$outputTokens; total_tokens=($inputTokens+$outputTokens); usage_available=($usage.Count -gt 0); passed=$passed; timed_out=$timedOut; exit_code=$process.ExitCode; agent_seconds=[Math]::Round($agentSeconds,3); completion_seconds=[Math]::Round($timer.Elapsed.TotalSeconds,3); test_output=$testOutput}
    $rows += $row
    $report = [ordered]@{model='gpt-6-luna'; codex_version=(& $codexPath --version | Out-String).Trim(); model_config='ignore-user-config; CLI defaults'; max_task_seconds=180; tasks=$rows}
    [IO.File]::WriteAllText((Join-Path $results 'codex-comparison.json'), ($report | ConvertTo-Json -Depth 12))
    [pscustomobject]$row | Select-Object task,total_tokens,usage_available,passed,timed_out,agent_seconds | ConvertTo-Json -Compress | Write-Output
}
