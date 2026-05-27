from __future__ import annotations


def build_external_tab_classes(deps: dict[str, object]) -> dict[str, type]:
    file_sorter_tab = deps['_load_file_sorter_tab_module']().build_file_sorter_tab_class(
        {
            'QWidget': deps['QWidget'],
            'QVBoxLayout': deps['QVBoxLayout'],
            'QHBoxLayout': deps['QHBoxLayout'],
            'QScrollArea': deps['QScrollArea'],
            'QLineEdit': deps['QLineEdit'],
            'QPushButton': deps['QPushButton'],
            'QLabel': deps['QLabel'],
            'QCheckBox': deps['QCheckBox'],
            'QPlainTextEdit': deps['QPlainTextEdit'],
            'QFileDialog': deps['QFileDialog'],
            'QApplication': deps['QApplication'],
            'QComboBox': deps['QComboBox'],
            'load_setting': deps['load_setting'],
            'save_setting': deps['save_setting'],
            'make_card': deps['make_card'],
            'make_transparent_row': deps['make_transparent_row'],
            'build_global_scrollbar_style': deps['build_global_scrollbar_style'],
            'show_themed_warning': deps['show_themed_warning'],
            'show_themed_error': deps['show_themed_error'],
            'show_themed_success': deps['show_themed_success'],
            'style_combo_popup': deps['style_combo_popup'],
            'get_file_sorter_module': deps['get_file_sorter_module'],
            'ROOT': deps['ROOT'],
        }
    )
    batch_rename_tab = deps['_load_name_tab_module']().build_batch_rename_tab_class(
        {
            'QWidget': deps['QWidget'],
            'QVBoxLayout': deps['QVBoxLayout'],
            'QHBoxLayout': deps['QHBoxLayout'],
            'QScrollArea': deps['QScrollArea'],
            'QLineEdit': deps['QLineEdit'],
            'QPushButton': deps['QPushButton'],
            'QLabel': deps['QLabel'],
            'QPlainTextEdit': deps['QPlainTextEdit'],
            'QFileDialog': deps['QFileDialog'],
            'QApplication': deps['QApplication'],
            'QComboBox': deps['QComboBox'],
            'load_setting': deps['load_setting'],
            'save_setting': deps['save_setting'],
            'make_card': deps['make_card'],
            'make_transparent_row': deps['make_transparent_row'],
            'build_global_scrollbar_style': deps['build_global_scrollbar_style'],
            'show_themed_warning': deps['show_themed_warning'],
            'show_themed_error': deps['show_themed_error'],
            'show_themed_success': deps['show_themed_success'],
            'style_combo_popup': deps['style_combo_popup'],
            'get_name_module': deps['get_name_module'],
            'ROOT': deps['ROOT'],
        }
    )
    video_downloader_tab = deps['_load_video_downloader_tab_module']().build_video_downloader_tab_class(
        {
            'QWidget': deps['QWidget'],
            'QVBoxLayout': deps['QVBoxLayout'],
            'QHBoxLayout': deps['QHBoxLayout'],
            'QScrollArea': deps['QScrollArea'],
            'QLineEdit': deps['QLineEdit'],
            'QPushButton': deps['QPushButton'],
            'QLabel': deps['QLabel'],
            'QCheckBox': deps['QCheckBox'],
            'QComboBox': deps['QComboBox'],
            'QPlainTextEdit': deps['QPlainTextEdit'],
            'QProgressBar': deps['QProgressBar'],
            'QFileDialog': deps['QFileDialog'],
            'QApplication': deps['QApplication'],
            'QObject': deps['QObject'],
            'QThread': deps['QThread'],
            'Signal': deps['Signal'],
            'load_setting': deps['load_setting'],
            'save_setting': deps['save_setting'],
            'make_card': deps['make_card'],
            'make_transparent_row': deps['make_transparent_row'],
            'build_global_scrollbar_style': deps['build_global_scrollbar_style'],
            'show_themed_warning': deps['show_themed_warning'],
            'show_themed_error': deps['show_themed_error'],
            'show_themed_success': deps['show_themed_success'],
            'style_combo_popup': deps['style_combo_popup'],
            'get_video_downloader_module': deps['get_video_downloader_module'],
            'ROOT': deps['ROOT'],
            'VIDEO_DOWNLOADER_DIR': deps['VIDEO_DOWNLOADER_DIR'],
        }
    )
    return {
        'FileSorterTab': file_sorter_tab,
        'BatchRenameTab': batch_rename_tab,
        'VideoDownloaderTab': video_downloader_tab,
    }

