import subprocess
import time

print("Starting SSH process...")
p = subprocess.Popen(['ssh', '-o', 'StrictHostKeyChecking=no', 'root@65.21.244.158', 'uptime'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
try:
    print("Sending password...")
    stdout, stderr = p.communicate(input='Cph181ko!!\n', timeout=20)
    print("STDOUT:", stdout)
    print("STDERR:", stderr)
except Exception as e:
    print("Error:", e)
    p.kill()
