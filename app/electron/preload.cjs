// 화면(React)에서 쓸 수 있는 기능만 좁게 노출한다
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  getStatus: () => ipcRenderer.invoke('get-status'),
  runAction: name => ipcRenderer.invoke('run-action', name),
  getSettings: () => ipcRenderer.invoke('get-settings'),
  setSettings: patch => ipcRenderer.invoke('set-settings', patch),
  quit: () => ipcRenderer.invoke('quit'),
  onActionLog: cb => {
    const handler = (_e, line) => cb(line);
    ipcRenderer.on('action-log', handler);
    return () => ipcRenderer.removeListener('action-log', handler);
  },
});
