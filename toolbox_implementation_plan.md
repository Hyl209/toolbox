# Hyl Tools Toolbox Implementation Plan

**Goal:** 鍦?`PROJECT_ROOT` 涓嬪疄鐜颁竴涓粺涓€鐨?PySide6 宸ュ叿绠变富绋嬪簭锛屾暣鍚?NCM鈫扢P3 涓?ZipAndPng 涓や釜宸ュ叿椤碉紝骞朵负鏈潵鏂板宸ュ叿淇濈暀鎵╁睍缁撴瀯銆?

**Architecture:** 閲囩敤 `QTabWidget` 浣滀负涓绘鏋讹紝姣忎釜宸ュ叿涓€涓嫭绔?QWidget銆傚鐢ㄧ幇鏈?CLI 鑴氭湰涓殑鍏变韩閫昏緫锛屼笉鍦?GUI 灞傞噸澶嶅疄鐜版牳蹇冨姛鑳姐€傞€氳繃 `QSettings` 璁颁綇鍚勫伐鍏风殑杈撳嚭鐩綍鍜屽父鐢ㄨ矾寰勩€?

**Tech Stack:** Python, PySide6, ncmdump, mutagen

---

### Task 1: 缁?zipandpng 鎻愪緵 GUI 鍙鐢ㄦ帴鍙?
**Objective:** 璁?zipandpng 涔熷儚 ncm 宸ュ叿涓€鏍锋湁娓呮櫚鍙鍏ョ殑鍏变韩鍑芥暟銆?

**Files:**
- Modify: `PROJECT_ROOT/zipandpng/tests/test_zipandpng.py`
- Modify: `PROJECT_ROOT/zipandpng/zipandpng.py`

**Step 1: Write failing test**
- 澧炲姞瀵?info 瑙ｆ瀽杈呭姪鍑芥暟/GUI 鍙皟鐢ㄥ寘瑁呯殑娴嬭瘯銆?

**Step 2: Run test to verify failure**
- 杩愯 zipandpng 娴嬭瘯
- Expected: FAIL

**Step 3: Write minimal implementation**
- 琛ュ厖杩斿洖缁撴瀯鍖栦俊鎭殑鍑芥暟锛屽噺灏?GUI 鍙兘鎶?stdout 鐨勯棶棰樸€?

**Step 4: Run test to verify pass**
- 杩愯 zipandpng 娴嬭瘯
- Expected: PASS

### Task 2: 涓哄伐鍏风鍏变韩璁剧疆鍐?RED 娴嬭瘯
**Objective:** 鍏堥攣瀹?toolbox 绾у埆鐨勮缃蹇嗗拰宸ュ叿鍙戠幇鎺ュ彛銆?

**Files:**
- Create: `PROJECT_ROOT/tests_toolbox.py`

**Step 1: Write failing test**
- 娴嬭瘯 toolbox 璁剧疆鍙繚瀛?璇诲彇 music 杈撳嚭鐩綍涓?zipandpng 甯哥敤璺緞
- 娴嬭瘯宸ュ叿椤靛畾涔夊垪琛ㄥ瓨鍦?music/zipandpng

**Step 2: Run test to verify failure**
- 杩愯 tests_toolbox.py
- Expected: FAIL锛屽洜涓?toolbox 妯″潡灏氫笉瀛樺湪

**Step 3: Write minimal implementation**
- 鍒涘缓 toolbox 妯″潡楠ㄦ灦涓?settings helper

**Step 4: Run test to verify pass**
- 杩愯 tests_toolbox.py
- Expected: PASS

### Task 3: 涓哄伐鍏烽〉琛屼负鍐?RED 娴嬭瘯
**Objective:** 閿佸畾 music 椤垫嫋鎷芥敹闆嗕笌 zipandpng 椤佃矾寰勫鐞嗚涓恒€?

**Files:**
- Create: `PROJECT_ROOT/tests_tool_pages.py`

**Step 1: Write failing test**
- 娴嬭瘯 music 椤垫敹闆?.ncm 鏂囦欢
- 娴嬭瘯 zipandpng 椤垫牎楠?cover/payload/output 杈撳叆

**Step 2: Run test to verify failure**
- 杩愯 tests_tool_pages.py
- Expected: FAIL

**Step 3: Write minimal implementation**
- 鎻愪緵涓嶄緷璧栫湡瀹炵獥鍙ｆ樉绀虹殑 page helper 鎴?widget 鏂规硶

**Step 4: Run test to verify pass**
- 杩愯 tests_tool_pages.py
- Expected: PASS

### Task 4: 瀹炵幇宸ュ叿绠变富鐣岄潰
**Objective:** 瀹屾垚 QTabWidget 涓荤獥鍙ｄ互鍙婁袱涓爣绛鹃〉銆?

**Files:**
- Create: `PROJECT_ROOT/hyl_toolbox.py`
- Possibly Create: `PROJECT_ROOT/toolbox_pages.py`
- Modify: `PROJECT_ROOT/tests_toolbox.py`
- Modify: `PROJECT_ROOT/tests_tool_pages.py`

**Step 1: Write failing test**
- 澧炲姞涓荤獥鍙ｅ寘鍚袱涓爣绛鹃〉銆佽缃仮澶嶃€佸熀纭€鍔ㄤ綔鍙皟鐢ㄧ殑鏂█

**Step 2: Run test to verify failure**
- 杩愯 toolbox/page 娴嬭瘯
- Expected: FAIL

**Step 3: Write minimal implementation**
- 瀹炵幇涓荤獥鍙ｃ€佷袱涓伐鍏烽〉銆佹棩蹇楀尯銆佽缃仮澶?

**Step 4: Run test to verify pass**
- 杩愯 toolbox/page 娴嬭瘯
- Expected: PASS

### Task 5: 闆嗘垚楠岃瘉
**Objective:** 鍦ㄥ凡瑁?PySide6 鐨勭幆澧冧腑瀹屾垚鏁翠綋楠岃瘉銆?

**Files:**
- Modify: `PROJECT_ROOT/findings.md`
- Modify: `PROJECT_ROOT/progress.md`

**Step 1: Run all relevant tests**
- 杩愯 music / zipandpng / toolbox 娴嬭瘯
- Expected: PASS

**Step 2: Manual verification**
- 鍚姩 GUI
- 妫€鏌ユ爣绛鹃〉瀛樺湪
- 妫€鏌?music 杈撳嚭鐩綍璁板繂
- 妫€鏌?zipandpng 鍩烘湰鎿嶄綔璺緞杈撳叆姝ｅ父

**Step 3: Document usage**
- 鏇存柊浣跨敤璇存槑涓庨獙璇佺粨鏋?

