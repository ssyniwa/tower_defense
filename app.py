import streamlit as st
import random
# 画面設定
st.set_page_config(page_title="Magic Defense", layout="centered")
# 属性定義: (画像接頭辞, 弱点属性)
ATTRIBUTES = {
    "fire": "stan",  # 火は草に強い
    "water": "fire",  # 水は火に強い
    "stan": "water"  # 草は水に強い
}
# --- ステージごとのルート定義 (各ステージのy座標リスト) ---
# ステージが進むほどルートを複雑に（蛇行させる）
STAGE_PATHS = {
    1: [3, 3, 3, 3, 3, 3], # 単純
    2: [3, 2, 2, 3, 4, 4], # 蛇行
    3: [3, 2, 3, 4, 3, 2], # 単純
    4: [3, 2, 1, 2, 3, 4], # 蛇行
    5: [3, 4, 3, 2, 1, 2], # 単純
    6: [3, 4, 5, 4, 3, 2], # 蛇行
    7: [3, 1, 3, 5, 3, 1], # 単純
    8: [1, 2, 3, 4, 5, 4], # 蛇行
    9: [5, 4, 3, 2, 1, 2], # 単純
    10: [2, 4, 2, 4, 2, 4], # 蛇行
}

def get_path(stage):
    # 定義がないステージはデフォルトでy=3の直線
    return STAGE_PATHS.get(stage, [3] * 6)
def get_enemies_for_stage(stage):
    """ステージに応じた数の敵を生成"""
    count = 3 + (stage - 1) * 2  # ステージ1は3体、以降2体ずつ増加
    enemies = []
    for i in range(count):
        # 属性をランダムに割り当て
        attr = random.choice(['fire', 'water', 'stan'])
        # 敵を少しずつずらして出現させる（xをマイナスに設定）
        enemies.append({
            'id': i, 'x': -i, 'y': get_path(stage)[0], 
            'attr': attr, 'hp': 5 + stage
        })
    return enemies
def reset_game_state(new_stage):
    st.session_state.game_state.update({
        'stage': new_stage,
        'towers': {},
        'money': 100,
        'enemies': get_enemies_for_stage(new_stage)
    })
def get_image_path(obj_type, stage, attr=None):
    """
    属性がある場合: images/fire_tower_stage1.png
    属性がない場合: images/path_stage1.png
    """
    if attr:
        return f"images/{attr}_{obj_type}_stage{stage}.png"
    return f"images/{obj_type}_stage{stage}.png"

def get_counter_attr(enemy_attr):
    """敵の属性に対する対抗属性（弱点を突く属性）を自動選択"""
    # 敵が"thunder"なら、それに強い"fire"を返す
    # 逆引きの辞書を作成
    counter_map = {v: k for k, v in ATTRIBUTES.items()}
    return counter_map[enemy_attr]
# --- 初期化 ---
if 'game_state' not in st.session_state:
    st.session_state.game_state = {
        'stage': 1,
        'money': 100,
        'tower_hp': 10,
        'game_over': False,
        'towers':  {},
        'enemies': [{'id': 0, 'x': 0, 'y': 3, 'attr': random.choice(list(ATTRIBUTES.keys())), 'hp': 5}]
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
    stage = state['stage']
    current_path = get_path(stage)
    
    for y in range(6):
        cols = st.columns(6)
        for x in range(6):
            with cols[x]:
                # 画像の決定ロジック
                img = None
                
                # 敵のチェック
                for e in state['enemies']:
                    if e['x'] == x and e['y'] == y:
                        img = get_image_path("enemy", stage, e['attr'])
                
                # 塔のチェック
                if not img and (x, y) in state['towers']:
                    attr = state['towers'][(x, y)]['attr']
                    img = get_image_path("tower", stage, attr)
                
                # 背景のチェック（道か草地か）
                if not img:
                    # current_path[x] がその列の道
                    if y == current_path[x]:
                        img = get_image_path("path", stage)
                    else:
                        img = get_image_path("grass", stage)
                
                st.image(img, use_container_width=True)
                # 建設ボタン
                if st.button("建", key=f"b_{x}_{y}"):
                    if y != 3 and (x, y) not in state['towers']:
                        target_enemy = next((e for e in state['enemies'] if abs(e['x'] - x) <= 1), None)
                        attr = get_counter_attr(target_enemy['attr']) if target_enemy else "fire"
                        state['towers'][(x, y)] = {'attr': attr}
                        state['money'] -= 50
                        st.rerun()

# --- ゲーム進行処理 ---
def game_logic():
    state = st.session_state.game_state
    path = get_path(state['stage'])
    
    # 射程強化：ステージが進むと攻撃範囲が広がる
    range_bonus = state['stage'] // 3 
    
    for pos, tower in state['towers'].items():
        for e in state['enemies']:
            # 射程判定：(1 + ボーナス) マス以内
            if abs(pos[0] - e['x']) <= (1 + range_bonus) and abs(pos[1] - e['y']) <= (1 + range_bonus):
                damage = 2 if ATTRIBUTES[tower['attr']] == e['attr'] else 1
                e['hp'] -= damage

    # 敵の移動とルート適用
    for e in state['enemies']:
        e['x'] += 1
        if e['x'] < 6:
            e['y'] = path[e['x']] # 定義されたルートを辿る
        elif e['x'] >= 6:
            state['tower_hp'] -= 1
            e['x'] = 0
# 3. 撃破と報酬
    new_enemies = []
    for e in state['enemies']:
        if e['hp'] > 0:
            new_enemies.append(e)
        else:
            state['money'] += 20
    state['enemies'] = new_enemies
    # 全滅判定
    if len(state['enemies']) == 0:
        reset_game_state(state['stage'] + 1)
    
    
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
