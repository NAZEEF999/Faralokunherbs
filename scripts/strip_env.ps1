# Strips the secret VALUES out of .env, keeping the variable names.
#
#  1. On first run, backs up the real secrets to .env.local (git-ignored)
#     so local development keeps working.
#  2. Rewrites .env as `NAME=` lines — safe to commit / copy/share.
#
# Run it again any time .env changes. It never prints a value.
$envFile = '.env'
$local   = '.env.local'

if (-not (Test-Path -LiteralPath $envFile)) {
    Write-Error "$envFile not found."; exit 1
}

if (-not (Test-Path -LiteralPath $local)) {
    Copy-Item -LiteralPath $envFile -Destination $local
    Write-Output "Backed up original secrets to $local (git-ignored)."
}

$out = foreach ($line in Get-Content -LiteralPath $envFile) {
    if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*') {
        "$($matches[1])="
    } elseif ($line.Trim() -eq '') {
        ''
    } else {
        $line   # comments and unknowns pass through untouched
    }
}

Set-Content -LiteralPath $envFile -Value $out -Encoding ascii
Write-Output "Stripped secrets from $envFile ($($out.Count) lines kept)."