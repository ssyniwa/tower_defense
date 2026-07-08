import streamlit as st

# 画面設定
st.set_page_config(page_title="Magic Defense", layout="centered")
# 属性定義: (画像接頭辞, 弱点属性)
ATTRIBUTES = {
    "fire": "stan",  # 火は草に強い
    "water": "fire",  # 水は火に強い
    "stan": "water"  # 草は水に強い
}

def get_image_path(obj_type, attr):
    """属性に基づいた画像パスを返す: images/fire_tower.png など"""
    return f"images/{attr}_{obj_type}.png"
# --- 初期化 ---
if 'game_state' not in st.session_state:
    st.session_state.game_state = {
        'stage': 1,
        'money': 100,
        'tower_hp': 10,
        'game_over': False,
        'towers': {}, # {(x, y): {'attr': 'fire'}}
        'enemies': [{'id': 0, 'x': 0, 'y': 3, 'attr': 'fire', 'hp': 5}]
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
    state = st.session_state.game_state
    for y in range(6):
        cols = st.columns(6)
        for x in range(6):
            with cols[x]:
                # 画像の決定ロジック
                if (x, y) in state['towers']:
                    attr = state['towers'][(x, y)]['attr']
                    img = get_image_path("tower", attr)
                else:
                    img = "images/path.png" if y == 3 else "images/grass.png"
                    for e in state['enemies']:
                        if e['x'] == x and e['y'] == y:
                            img = get_image_path("enemy", e['attr'])
                
                st.image(img, use_container_width=True)
                
                # 建設ボタン（属性選択肢を表示）
                if st.button("建", key=f"b_{x}_{y}"):
                    # 簡易UI: 属性選択を表示などにするのがベター
                    state['towers'][(x, y)] = {'attr': 'fire'} 
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
            if abs(pos[0] - e['x']) <= 1 and abs(pos[1] - e['y']) <= 1:
                # 属性相性ボーナス
                damage = 2 if ATTRIBUTES[tower['attr']] == e['attr'] else 1
                e['hp'] -= damage
    # 3. 撃破と報酬
    new_enemies = []
    for e in state['enemies']:
        if e['hp'] > 0:
            new_enemies.append(e)
        else:
            state['money'] += 20
    state['enemies'] = new_enemies
    # ステージ進行処理
    if len(state['enemies']) == 0:
        state['stage'] += 1
        # 新しい敵を配置（ステージが進むと属性がバラける）
        state['enemies'].append({'id': state['stage'], 'x': 0, 'y': 3, 'attr': 'water', 'hp': 5 + state['stage']})
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
