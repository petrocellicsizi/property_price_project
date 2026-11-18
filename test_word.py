import subprocess
ps_code = ' = New-Object -ComObject Word.Application; Write-Host .Version; .Quit()'
with open('test_word.ps1', 'w') as f:
    f.write(ps_code)
res = subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-File', 'test_word.ps1'], capture_output=True, text=True)
print('STDOUT:', res.stdout)
print('STDERR:', res.stderr)
