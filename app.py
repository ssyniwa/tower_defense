import streamlit as st

# 画面設定
st.set_page_config(page_title="Magic Defense", layout="centered")

# --- 初期化 ---
if 'game_state' not in st.session_state:
    st.session_state.game_state = {
        'tower_hp': 5,
        'money': 100,
        'enemies': [{'id': 0, 'x': 0, 'y': 3, 'hp': 3}],
        'towers': {},
        'game_over': False
    }

# --- カスタムCSS（スマホ最適化） ---
st.markdown("""
<style>
    div[data-testid="column"] { padding: 0 !important; }
    .stButton>button { 
        width: 100%; aspect-ratio: 1/1; 
        font-size: 20px; padding: 0; 
        border-radius: 5px; 
    }
</style>
""", unsafe_allow_html=True)

state = st.session_state.game_state

# --- 描画ロジック ---
def draw_grid():
    for y in range(6):
        cols = st.columns(6)
        for x in range(6):
            with cols[x]:
                # 画像の選択
                img = "images/grass.png"
                if y == 3: img = "images/path.png"
                if (x, y) in state['towers']: img = "images/tower.png"
                for e in state['enemies']:
                    if e['x'] == x and e['y'] == y: img = "images/enemy.png"
                
                # 画像表示
                st.image(img, use_container_width=True)
                
                # クリックボタン（画像のすぐ下に配置）
                if st.button("建", key=f"b_{x}_{y}"):
                    if y != 3 and (x, y) not in state['towers'] and state['money'] >= 50:
                        state['towers'][(x, y)] = True
                        state['money'] -= 50
                        st.rerun()

# --- ゲーム進行処理 ---
def game_logic():
    for e in state['enemies']:
        e['x'] += 1
        if e['x'] >= 6:
            state['tower_hp'] -= 1
            e['x'] = 0
    
    # 2. タワーの攻撃
    for pos, tower in state['towers'].items():
        for e in state['enemies']:
            # 隣接8マス以内なら攻撃
            if abs(pos[0] - e['x']) <= 1 and abs(pos[1] - e['y']) <= 1:
                e['hp'] -= 1
    
    # 3. 撃破と報酬
    new_enemies = []
    for e in state['enemies']:
        if e['hp'] > 0:
            new_enemies.append(e)
        else:
            state['money'] += 20
    state['enemies'] = new_enemies
    
    # 4. ゲームオーバー判定
    if state['tower_hp'] <= 0: state['game_over'] = True

# --- メイン画面 ---
st.title("🏰 Magic Defense")
st.write(f"HP: {state['tower_hp']} | Gold: {state['money']}")

if not state['game_over']:
    draw_grid()
    if st.button("▶ 次のターン"):
        game_logic()
        st.rerun()
else:
    st.error("GAME OVER!")
    if st.button("リトライ"):
        st.session_state.game_state = None
        st.rerun()
