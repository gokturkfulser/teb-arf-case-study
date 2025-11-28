# Test script for Docker services

Write-Host ""
Write-Host "=== Testing Docker Services ===" -ForegroundColor Cyan
Write-Host ""

# Test STT Service
Write-Host "1. Testing STT Service (port 8001)..." -ForegroundColor Yellow
try {
    $stt = Invoke-RestMethod -Uri "http://localhost:8001/health" -Method Get
    Write-Host "   [OK] STT Service: $($stt.status)" -ForegroundColor Green
    Write-Host "   - Model loaded: $($stt.model_loaded)" -ForegroundColor Gray
    Write-Host "   - Device: $($stt.device)" -ForegroundColor Gray
} catch {
    Write-Host "   [FAIL] STT Service: Failed - $_" -ForegroundColor Red
}

# Test RAG Service
Write-Host ""
Write-Host "2. Testing RAG Service (port 8002)..." -ForegroundColor Yellow
try {
    $rag = Invoke-RestMethod -Uri "http://localhost:8002/health" -Method Get
    Write-Host "   [OK] RAG Service: $($rag.status)" -ForegroundColor Green
    Write-Host "   - Index size: $($rag.index_size)" -ForegroundColor Gray
    Write-Host "   - Index name: $($rag.index_name)" -ForegroundColor Gray
} catch {
    Write-Host "   [FAIL] RAG Service: Failed - $_" -ForegroundColor Red
}

# Test Gateway Service
Write-Host ""
Write-Host "3. Testing Gateway Service (port 8000)..." -ForegroundColor Yellow
try {
    $gateway = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
    Write-Host "   [OK] Gateway Service: $($gateway.status)" -ForegroundColor Green
    if ($gateway.stt_service) {
        Write-Host "   - STT: $($gateway.stt_service)" -ForegroundColor Gray
    }
    if ($gateway.rag_service) {
        if ($gateway.rag_service.GetType().Name -eq "Hashtable") {
            Write-Host "   - RAG: $($gateway.rag_service.status)" -ForegroundColor Gray
        } else {
            Write-Host "   - RAG: $($gateway.rag_service)" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "   [FAIL] Gateway Service: Failed - $_" -ForegroundColor Red
}

# Test Text Query
Write-Host ""
Write-Host "4. Testing Text Query via Gateway..." -ForegroundColor Yellow
try {
    $bodyObject = @{
        question = "iphone kampanyası nedir"
        k = 3
    }
    $bodyJson = $bodyObject | ConvertTo-Json
    
    $query = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/text-query" -Method Post -Body $bodyJson -ContentType "application/json"
    Write-Host "   [OK] Query successful" -ForegroundColor Green
    if ($query.answer) {
        $answerLength = $query.answer.Length
        if ($answerLength -gt 100) {
            $answerPreview = $query.answer.Substring(0, 100) + "..."
        } else {
            $answerPreview = $query.answer
        }
        Write-Host "   - Answer: $answerPreview" -ForegroundColor Gray
    }
    if ($query.num_sources) {
        Write-Host "   - Sources: $($query.num_sources)" -ForegroundColor Gray
    }
} catch {
    Write-Host "   [FAIL] Query failed - $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Test Complete ===" -ForegroundColor Cyan
Write-Host ""
