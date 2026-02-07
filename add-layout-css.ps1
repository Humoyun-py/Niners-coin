$htmlFiles = Get-ChildItem -Path "frontend/pages" -Recurse -Filter "*.html"
$layoutLink = '    <link rel="stylesheet" href="/styles/layout.css">'
$updated = 0
$skipped = 0

foreach ($file in $htmlFiles) {
    try {
        $content = Get-Content -Path $file.FullName -Raw -Encoding UTF8
        
        # Check if layout.css already exists
        if ($content -match 'layout\.css') {
            Write-Host "⏭️  Skipped (already has layout.css): $($file.Name)" -ForegroundColor Yellow
            $skipped++
            continue
        }
        
        # Check if main.css exists to add layout.css after it
        if ($content -match '<link rel="stylesheet" href="/styles/main\.css">') {
            $newContent = $content -replace '(<link rel="stylesheet" href="/styles/main\.css">)', "`$1`r`n$layoutLink"
            Set-Content -Path $file.FullName -Value $newContent -Encoding UTF8 -NoNewline
            Write-Host "✅ Updated: $($file.FullName)" -ForegroundColor Green
            $updated++
        } else {
            Write-Host "⚠️  No main.css found in: $($file.Name)" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Error updating $($file.Name): $_" -ForegroundColor Red
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "✨ Total files updated: $updated" -ForegroundColor Green
Write-Host "⏭️  Total files skipped: $skipped" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
