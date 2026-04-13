import { spawn } from 'child_process';
const child = spawn('ssh', ['-o', 'StrictHostKeyChecking=no', 'root@65.21.244.158', 'uptime'], {
  stdio: ['pipe', 'pipe', 'pipe']
});
child.stdout.on('data', (data) => console.log('STDOUT: ' + data));
child.stderr.on('data', (data) => {
    const str = data.toString();
    console.log('STDERR: ' + str);
    if (str.toLowerCase().includes('password')) {
        console.log('Password prompt detected, sending password...');
        child.stdin.write('Cph181ko!!\n');
    }
});
child.on('close', (code) => console.log('Process exited with code: ' + code));
