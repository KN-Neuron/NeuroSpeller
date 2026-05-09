from brainaccess.core.eeg_manager import EEGManager
print([m for m in dir(EEGManager) if not m.startswith('_')])