"""Startup regression checks; no display or ROM is required."""
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import ffl3_editor as editor


class LauncherTests(unittest.TestCase):
    def test_empty_argument_opens_picker_and_cancel_closes(self):
        for argument in (None, ''):
            with self.subTest(argument=argument):
                root = Mock()
                with patch('tkinter.Tk', return_value=root), patch('tkinter.filedialog.askopenfilename', return_value='') as picker, patch.object(editor, 'load_rom') as load:
                    self.assertIsNone(editor.gui(argument, 'project_fr.json'))
                picker.assert_called_once()
                load.assert_not_called()
                root.destroy.assert_called_once()

    def test_explicit_path_skips_picker_and_reports_read_error(self):
        root = Mock()
        with patch('tkinter.Tk', return_value=root), patch('tkinter.filedialog.askopenfilename') as picker, patch('tkinter.messagebox.showerror') as error, patch.object(editor, 'load_rom', side_effect=PermissionError('Acces refuse')) as load:
            self.assertIs(editor.gui('C:/ROMs/original.gb', 'project_fr.json'), False)
        picker.assert_not_called()
        load.assert_called_once_with('C:/ROMs/original.gb')
        error.assert_called_once()
        root.destroy.assert_called_once()

    def test_chosen_path_is_loaded(self):
        root = Mock()
        with patch('tkinter.Tk', return_value=root), patch('tkinter.filedialog.askopenfilename', return_value='C:/ROMs/jeu original.gb'), patch('tkinter.messagebox.showerror'), patch.object(editor, 'load_rom', side_effect=ValueError('ROM invalide')) as load:
            self.assertIs(editor.gui('', 'project_fr.json'), False)
        load.assert_called_once_with('C:/ROMs/jeu original.gb')

    def test_cli_default_project_is_beside_editor(self):
        with patch.object(sys, 'argv', ['ffl3_editor.py', 'gui']), patch.object(editor, 'gui') as gui:
            editor.main()
        gui.assert_called_once_with(None, str(Path(editor.__file__).resolve().with_name('project_fr.json')))

    def test_previous_cli_arguments_still_work(self):
        with patch.object(sys, 'argv', ['ffl3_editor.py', 'gui', 'C:/jeu original.gb', 'C:/projet fr.json']), patch.object(editor, 'gui') as gui:
            editor.main()
        gui.assert_called_once_with('C:/jeu original.gb', 'C:/projet fr.json')


if __name__ == '__main__':
    unittest.main()
