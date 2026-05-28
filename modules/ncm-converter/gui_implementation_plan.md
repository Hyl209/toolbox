# NCM GUI Implementation Plan

**Goal:** 涓虹幇鏈?NCM 杞?MP3 宸ュ叿澧炲姞涓€涓?PySide6 鍥惧舰鐣岄潰锛屾敮鎸佹壒閲忔嫋鎷姐€佹寚瀹氫笖璁板繂杈撳嚭鐩綍銆佹壒閲忚浆鎹㈠拰鏃ュ織鏄剧ず銆?
**Architecture:** 澶嶇敤 `ncm_to_mp3.py` 涓殑鍏变韩杞崲閫昏緫锛屾妸 GUI 鏀惧湪 `ncm_gui.py`銆備娇鐢?`QSettings` 淇濆瓨杈撳嚭鐩綍锛岄伩鍏嶆妸鐘舵€佸啓姝诲湪鐣岄潰灞傘€?
**Tech Stack:** Python, PySide6, ncmdump, mutagen

---

### Task 1: 涓哄叡浜€昏緫琛ュ彲娴嬭瘯鎺ュ彛
**Objective:** 璁?GUI 鍙洿鎺ュ鐢ㄦ枃浠舵敹闆嗕笌杞崲閫昏緫銆?
**Files:**
- Modify: `modules/ncm-converter/ncm_to_mp3.py`
- Modify: `modules/ncm-converter/tests_ncm_to_mp3.py`

**Step 1: Write failing test**
- 澧炲姞瀵圭洰褰曟壂鎻忋€侀潪 ncm 杩囨护銆侀噸澶嶈矾寰勫幓閲嶅彲璋冪敤鎺ュ彛鐨勬祴璇曘€?
**Step 2: Run test to verify failure**
- 杩愯鎵嬪姩 test_* runner
- Expected: FAIL锛屽洜涓烘帴鍙ｅ皻鏈畬鏁存彁渚?
**Step 3: Write minimal implementation**
- 鎻愪緵 GUI 鍙皟鐢ㄧ殑鏀堕泦鍑芥暟涓庢壒閲忚浆鎹㈠嚱鏁?
**Step 4: Run test to verify pass**
- 杩愯 tests_ncm_to_mp3.py
- Expected: PASS

### Task 2: 涓?GUI 鐘舵€佷笌璁剧疆鍐?RED 娴嬭瘯
**Objective:** 鍏堥攣瀹氣€滆緭鍑虹洰褰曡蹇嗏€濆拰鈥滄嫋鎷芥坊鍔犳枃浠垛€濊涓恒€?
**Files:**
- Create: `modules/ncm-converter/tests_ncm_gui.py`

**Step 1: Write failing test**
- 娴嬭瘯淇濆瓨/璇诲彇杈撳嚭鐩綍璁剧疆
- 娴嬭瘯娣诲姞鏂囦欢鍜岀洰褰曞悗鑳芥敹闆嗗埌 .ncm

**Step 2: Run test to verify failure**
- 杩愯 tests_ncm_gui.py
- Expected: FAIL锛屽洜涓?`ncm_gui.py` 灏氫笉瀛樺湪

**Step 3: Write minimal implementation**
- 鍒涘缓 GUI 鏂囦欢骞跺疄鐜版渶灏忓彲娴嬬被

**Step 4: Run test to verify pass**
- 杩愯 tests_ncm_gui.py
- Expected: PASS

### Task 3: 瀹炵幇 PySide6 涓荤晫闈?**Objective:** 瀹屾垚鎷栨嫿鍖恒€佹枃浠跺垪琛ㄣ€佽緭鍑虹洰褰曢€夋嫨銆佸紑濮嬭浆鎹€佽繘搴︿笌鏃ュ織銆?
**Files:**
- Create: `modules/ncm-converter/ncm_gui.py`
- Modify: `modules/ncm-converter/tests_ncm_gui.py`

**Step 1: Write failing test**
- 澧炲姞寮€濮嬭浆鎹㈠墠蹇呴』鏈夎緭鍑虹洰褰曘€佽浆鎹㈠悗鏃ュ織鏇存柊绛夋柇瑷€

**Step 2: Run test to verify failure**
- 杩愯 GUI 娴嬭瘯
- Expected: FAIL

**Step 3: Write minimal implementation**
- 瀹炵幇涓荤獥鍙ｅ拰鏍稿績妲藉嚱鏁?
**Step 4: Run test to verify pass**
- 杩愯 GUI 娴嬭瘯
- Expected: PASS

### Task 4: 闆嗘垚楠岃瘉
**Objective:** 瀹夎 GUI 渚濊禆骞跺仛鏍锋湰鎵嬪伐楠岃瘉銆?
**Files:**
- Modify: `modules/ncm-converter/progress.md`
- Modify: `modules/ncm-converter/findings.md`

**Step 1: Install dependency**
- 鍦?`.venv` 瀹夎 `PySide6`

**Step 2: Run all tests**
- 杩愯 `tests_ncm_to_mp3.py` 鍜?`tests_ncm_gui.py`
- Expected: PASS

**Step 3: Manual verification**
- 鐢ㄦ牱鏈洰褰曢獙璇?GUI 鍙惎鍔ㄣ€佸彲璁颁綇杈撳嚭鐩綍銆佸彲杞崲鏂囦欢

**Step 4: Document usage**
- 鏇存柊浣跨敤璇存槑涓庨獙璇佺粨鏋?
