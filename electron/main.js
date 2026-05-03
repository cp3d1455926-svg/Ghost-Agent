const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let ghostProcess;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    title: 'Ghost Agent',
    icon: path.join(__dirname, 'assets', 'icon.png'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    backgroundColor: '#08080c',
    show: false,
  });

  // Load the Ghost Agent Web UI
  mainWindow.loadURL('http://localhost:26602');

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
    if (ghostProcess) {
      ghostProcess.kill();
    }
  });
}

function startGhostAgent() {
  // Start the Python Ghost Agent backend
  const pythonPath = path.join(__dirname, '..', 'python', 'python.exe');
  const scriptPath = path.join(__dirname, '..', 'ghost_v31.py');
  
  ghostProcess = spawn(pythonPath, [scriptPath, '--web'], {
    cwd: path.join(__dirname, '..'),
    stdio: 'pipe',
  });

  ghostProcess.stdout.on('data', (data) => {
    console.log(`[Ghost] ${data}`);
  });

  ghostProcess.stderr.on('data', (data) => {
    console.error(`[Ghost Error] ${data}`);
  });

  ghostProcess.on('close', (code) => {
    console.log(`Ghost Agent exited with code ${code}`);
  });
}

app.whenReady().then(() => {
  startGhostAgent();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    if (ghostProcess) ghostProcess.kill();
    app.quit();
  }
});

app.on('before-quit', () => {
  if (ghostProcess) ghostProcess.kill();
});

// IPC handlers
ipcMain.handle('get-version', () => {
  return '3.1.0';
});
