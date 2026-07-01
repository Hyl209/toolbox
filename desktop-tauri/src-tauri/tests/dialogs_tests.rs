use desktop_tauri_lib::dialogs::{normalize_dialog_filters, DialogFilter};

#[test]
fn normalizes_dialog_filters_for_file_picker() {
    let filters = normalize_dialog_filters(vec![
        DialogFilter {
            name: "Images".into(),
            extensions: vec![".png".into(), " JPG ".into(), "".into()],
        },
        DialogFilter {
            name: "Empty".into(),
            extensions: vec![],
        },
    ]);

    assert_eq!(filters.len(), 1);
    assert_eq!(filters[0].name, "Images");
    assert_eq!(filters[0].extensions, vec!["png", "jpg"]);
}
