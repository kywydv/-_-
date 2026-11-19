const vscode = require('vscode');
const path = require('path');
const {PythonDebugSession} = require('./siplDebug');

function activate(context) {
  context.subscriptions.push(vscode.debug.registerDebugConfigurationProvider('sipl', {
    resolveDebugConfiguration(folder, config) {
      if (!config.type) config.type = 'sipl';
      if (!config.request) config.request = 'launch';
      if (!config.name) config.name = 'Launch SIPL';
      if (!config.program && vscode.window.activeTextEditor)
        config.program = vscode.window.activeTextEditor.document.fileName;
      if (!config.program) {
        vscode.window.showErrorMessage('Відкрийте .sipl файл для налагодження.');
        return undefined;
      }
      return config;
    }
  }));
  context.subscriptions.push(vscode.debug.registerDebugAdapterDescriptorFactory('sipl', {
    createDebugAdapterDescriptor() {
      const python = process.platform === 'win32' ? 'python' : 'python3';
      const script = path.join(context.extensionPath, 'dap_server.py');
      return new vscode.DebugAdapterExecutable(python, [script]);
    }
  }));
  context.subscriptions.push(vscode.commands.registerCommand('sipl.runCurrent', async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;
    const doc = editor.document;
    await doc.save();
    const terminal = vscode.window.createTerminal('SIPL');
    terminal.show();
    terminal.sendText(`python -m sipl.cli run "${doc.fileName}"`);
  }));
}
function deactivate() {}
module.exports = {activate, deactivate};
