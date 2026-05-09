# PDF 澶勭悊璁捐鏂囨。

## 鍔熻兘鐩爣
鍦?`hyl tools` 涓柊澧炰竴涓笌 `music/`銆乣mp4-mp3/`銆乣zipandpng/`銆乣image-convert/` 鍚岀骇鐨勭嫭绔嬫ā鍧?`pdf-tools/`锛屾彁渚?PDF 杞浘鐗囥€佸 PDF 鍚堝苟銆佸崟 PDF 鎷嗗垎銆丳DF 杞?Word锛堢湡瀹?`.docx`锛夈€佷互鍙娾€滃厛鎻愭枃瀛楀眰锛屾彁涓嶅埌鍐?OCR鈥濈殑鍩虹鏂囧瓧鎻愬彇鑳藉姏銆?

## 鐩綍璁捐

鏂板鐩綍锛歚PROJECT_ROOT/pdf-tools/`

璁″垝鏂囦欢锛?
- `pdf-tools/converter.py`锛歅DF 澶勭悊鏍稿績閫昏緫
- `pdf-tools/README.md`锛氬瓙妯″潡璇存槑
- `pdf-tools/tests_pdf_tools.py`锛氭牳蹇冮€昏緫娴嬭瘯
- `pdf-tools/task_plan.md`
- `pdf-tools/findings.md`
- `pdf-tools/progress.md`

鏍圭洰褰曡仈鍔ㄤ慨鏀癸細
- `hyl_toolbox.py`锛氭柊澧?PDF 澶勭悊 Tab銆佹ā鍧楀姞杞姐€佽〃鍗曟牎楠屼笌璋冪敤鍏ュ彛
- `tests_tool_pages.py` / `tests_toolbox.py`锛氳ˉ GUI/杈呭姪閫昏緫娴嬭瘯
- `README.md`锛氳ˉ鍏呮柊妯″潡璇存槑
- `HylToolbox.spec`锛氭妸 `pdf-tools/converter.py` 涓€骞舵墦鍖?

## GUI 璁捐

渚ц竟鏍忔柊澧炰竴椤癸細`PDF澶勭悊`

鏂伴〉闈㈠唴瀹癸細
1. 鎷栨嫿鍖猴細鏀寔鎷栧叆涓€涓垨澶氫釜 PDF
2. 鎿嶄綔绫诲瀷閫夋嫨锛歅DF杞浘鐗?/ 鍚堝苟PDF / 鎷嗗垎PDF / PDF杞琖ord / 鎻愬彇鏂囧瓧
3. 杈撳嚭鐩綍閫夋嫨
4. PDF 杞浘鐗囧弬鏁帮細杈撳嚭鏍煎紡 PNG/JPG銆丏PI
5. 鎷嗗垎鍙傛暟锛氶〉鐮佽寖鍥达紙濡?`1-3,5,8-10`锛?
6. OCR 閫夐」锛氳嚜鍔ㄦā寮忥紙鍏堟枃瀛楀眰鍚?OCR锛?
7. 寮€濮嬪鐞嗘寜閽?
8. 杩涘害鏉?+ 鏃ュ織妗?

## 琛屼负瑙勫垯

### 杈撳叆瑙勫垯
- 鎺ュ彈锛歚.pdf`
- 鍚堝苟鍔熻兘鍏佽澶氫釜 PDF
- 鎷嗗垎 / 杞浘鐗?/ 杞?Word / 鎻愬彇鏂囧瓧 榛樿闈㈠悜鍗?PDF
- 鏀寔鏂囦欢澶归€掑綊鏀堕泦 PDF锛屼絾 GUI 棣栫増浠ユ枃浠舵嫋鍏ヤ负涓?

### PDF杞浘鐗?
- 姣忛〉瀵煎嚭涓€寮犲浘鐗?
- 杈撳嚭鏂囦欢鍚嶏細`鍘熸枃浠跺悕_page_001.png`
- 鏀寔 PNG / JPG
- DPI 榛樿 150锛屽彲璋冮珮鐢ㄤ簬 OCR 鍓嶉澶勭悊

### 澶?PDF 鍚堝苟
- 鎸夌敤鎴烽€夋嫨椤哄簭鍚堝苟
- 榛樿杈撳嚭锛歚merged.pdf`
- 鑻ラ噸鍚嶅垯鍏佽鑷姩杩藉姞缂栧彿

### 鍗?PDF 鎷嗗垎
- 鏀寔鎸夐〉鑼冨洿鎷嗗嚭澶氫釜鍗曢〉 PDF
- 棣栫増浼樺厛鏀寔椤电爜鑼冨洿鏂囨湰杈撳叆
- 杈撳嚭鏂囦欢鍚嶏細`鍘熸枃浠跺悕_page_001.pdf`

### PDF 杞?Word
- 杈撳嚭鐪熷疄 `.docx`
- 浼樺厛鎻愬彇 PDF 鍘熺敓鏂囧瓧灞?
- 鑻ラ〉鏃犲彲鎻愬彇鏂囧瓧锛屽垯鎶婅椤佃浆鍥剧墖鍚庤蛋 OCR
- 棣栫増浠モ€滄寜椤甸『搴忓啓鍏ユ钀芥枃鏈€濅负涓伙紝涓嶈拷姹傚鏉傛帓鐗堣繕鍘?

### 鏂囧瓧鎻愬彇
- 杈撳嚭 `.txt`
- 瑙勫垯锛氬厛鎻愭枃瀛楀眰锛岃嫢涓虹┖鎴栧彧鏈夋瀬灏戠┖鐧藉瓧绗︼紝鍒欏洖閫€ OCR
- OCR 缁撴灉鎸夐〉鎷兼帴锛屽苟淇濈暀椤靛垎闅旀爣璁?

## 鎶€鏈柟妗?

### 渚濊禆
- `pypdf`锛歅DF 鍚堝苟銆佹媶鍒?
- `PyMuPDF`锛坄fitz`锛夛細璇诲彇椤甸潰銆佹覆鏌撲负鍥剧墖銆佹彁鍙栧熀纭€鏂囨湰
- `python-docx`锛氱敓鎴?`.docx`
- `pytesseract`锛歄CR
- 澶栭儴渚濊禆锛氱郴缁?`tesseract` 鍛戒护锛堣嫢鏃犲垯鍙敮鎸佹枃瀛楀眰鎻愬彇骞剁粰鍑烘彁绀猴級

### 鏍稿績瀹炵幇鎬濊矾
`converter.py` 鎻愪緵杩欎簺鑳藉姏锛?
- `collect_pdf_inputs(paths)`锛氭敹闆?PDF
- `probe_tesseract()`锛氭鏌?OCR 渚濊禆
- `parse_page_ranges(raw, total_pages)`锛氳В鏋愰〉鐮佽寖鍥?
- `merge_pdfs(inputs, output_path)`
- `split_pdf(input_path, output_dir, ranges)`
- `pdf_to_images(input_path, output_dir, image_format, dpi)`
- `extract_page_text(page, ocr_fallback)`
- `extract_text_to_txt(input_path, output_path, use_ocr_fallback=True)`
- `pdf_to_docx(input_path, output_path, use_ocr_fallback=True)`

## 娴嬭瘯璁捐

### 鏍稿績閫昏緫娴嬭瘯
鍦?`pdf-tools/tests_pdf_tools.py` 涓鐩栵細
- PDF 杈撳叆鏀堕泦杩囨护
- 椤电爜鑼冨洿瑙ｆ瀽
- 鍚堝苟/鎷嗗垎鍙傛暟鏍￠獙
- Tesseract 缂哄け鏃剁殑鎺㈡祴鎻愮ず
- Word / TXT 杈撳嚭璺緞鐢熸垚
- OCR 鍥為€€绛栫暐閫夋嫨閫昏緫

璇存槑锛氫紭鍏堣鐩?Python 灞傞€昏緫銆佽矾寰勩€佸弬鏁板拰鍥為€€绛栫暐锛涗笉寮轰緷璧栨瘡鍙版満鍣ㄩ兘鐪熷疄瑁呭ソ OCR銆?

### GUI 娴嬭瘯
鍦ㄦ牴鐩綍娴嬭瘯閲岃ˉ锛?
- 鏂?Tab 鏄惁鍑虹幇鍦ㄤ晶杈规爮
- 鎿嶄綔绫诲瀷鍒囨崲鏄惁鎴愬姛
- 绌鸿〃鍗曟牎楠屾槸鍚︽纭?
- PDF 鎷栨嫿鎽樿鏄惁姝ｇ‘

## 椋庨櫓涓庤竟鐣?
- OCR 璐ㄩ噺鍙栧喅浜庢壂鎻忔竻鏅板害涓?Tesseract 瀹夎鎯呭喌
- `.docx` 棣栫増鍋忊€滄枃鏈鍑衡€濓紝涓嶆槸鐗堝紡绾ц繕鍘?
- 鎵弿浠?OCR 浼氭瘮鏂囧瓧灞傛彁鍙栨參寰堝
- 鍥剧墖鍨?PDF 鑻ユ病瑁?Tesseract锛學ord/TXT 鍙兘鎻愮ず缂哄皯 OCR 鑳藉姏

## 鎺ㄨ崘瀹炵幇椤哄簭
1. 鏂板缓 `pdf-tools/` 鐩綍鍜屾牳蹇?`converter.py`
2. 鍏堝啓绾€昏緫娴嬭瘯
3. 瀹炵幇鍚堝苟 / 鎷嗗垎 / 璺緞 / OCR 鎺㈡祴
4. 鎺ュ叆 `hyl_toolbox.py` 鏂?Tab
5. 鏇存柊鎵撳寘閰嶇疆 `HylToolbox.spec`
6. 鏇存柊鎬?README 涓庡瓙妯″潡 README
7. 璺戞祴璇曢獙璇?

