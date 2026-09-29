# Servidor local AUTOPORTANTE del visor Catastro Boyaca (no requiere Python ni internet).
# Usa solo PowerShell, incluido en Windows. Sirve la carpeta visor\ en http://localhost:8766/
# y la carpeta docs\ en http://localhost:8766/docs/ (documentos descargados).
# Uso: doble clic en ABRIR_VISOR_OFFLINE.bat (o: powershell -ExecutionPolicy Bypass -File servidor_offline.ps1)
param([int]$Puerto = 8766)

$Raiz  = Split-Path -Parent $MyInvocation.MyCommand.Path
$Visor = Join-Path $Raiz 'visor'
$Docs  = Join-Path $Raiz 'docs'
$Tipos = @{
  '.html'='text/html; charset=utf-8'; '.js'='application/javascript; charset=utf-8'; '.css'='text/css; charset=utf-8';
  '.json'='application/json; charset=utf-8'; '.geojson'='application/geo+json'; '.png'='image/png'; '.jpg'='image/jpeg';
  '.jpeg'='image/jpeg'; '.svg'='image/svg+xml'; '.pdf'='application/pdf'; '.csv'='text/csv; charset=utf-8';
  '.xlsx'='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'; '.xls'='application/vnd.ms-excel';
  '.docx'='application/vnd.openxmlformats-officedocument.wordprocessingml.document'; '.ico'='image/x-icon'
}

$Oyente = New-Object System.Net.HttpListener
$Oyente.Prefixes.Add("http://localhost:$Puerto/")
try { $Oyente.Start() } catch { Write-Host "No se pudo abrir el puerto $Puerto (¿ya hay un visor abierto?)."; Start-Process "http://localhost:$Puerto/"; exit }
Write-Host "Visor OFFLINE en http://localhost:$Puerto/  (cierre esta ventana para apagarlo)"
Start-Process "http://localhost:$Puerto/"

while ($Oyente.IsListening) {
  $ctx = $Oyente.GetContext()
  $res = $ctx.Response
  try {
    $ruta = [Uri]::UnescapeDataString($ctx.Request.Url.AbsolutePath)
    if ($ruta.StartsWith('/docs/')) { $base = $Docs; $rel = $ruta.Substring(6) } else { $base = $Visor; $rel = $ruta.TrimStart('/') }
    if ($rel -eq '' -or $rel.EndsWith('/')) { $rel += 'index.html' }
    $archivo = [System.IO.Path]::GetFullPath((Join-Path $base $rel))
    if (-not $archivo.StartsWith([System.IO.Path]::GetFullPath($base)) -or -not (Test-Path -LiteralPath $archivo -PathType Leaf)) {
      $res.StatusCode = 404
      $b = [Text.Encoding]::UTF8.GetBytes('No encontrado')
      $res.OutputStream.Write($b, 0, $b.Length)
    } else {
      $ext = [System.IO.Path]::GetExtension($archivo).ToLower()
      $res.ContentType = if ($Tipos.ContainsKey($ext)) { $Tipos[$ext] } else { 'application/octet-stream' }
      $res.Headers.Add('Cache-Control', 'no-cache')
      $fs = [System.IO.File]::OpenRead($archivo)
      $res.ContentLength64 = $fs.Length
      $fs.CopyTo($res.OutputStream)
      $fs.Close()
    }
  } catch { } finally { try { $res.OutputStream.Close() } catch { } }
}
