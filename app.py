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
        'money': 150,
        'tower_hp': 10,
        'game_over': False,
        'towers':  {},
        'enemies': get_enemies_for_stage(1)
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
                
                is_path = (y == current_path[x])
                
                st.image(img, use_container_width=True)
                
                if (x, y) in state['towers']:
                    tower_hp = state['towers'][(x, y)]['hp']
                    # HPの割合を計算 (MAX 10として)
                    st.progress(min(tower_hp / 10, 1.0))
                if y != current_path[x]:
                    # 既に塔があるか確認
                    if (x, y) not in state['towers']:
                        # 建設時の処理（game_logic付近を修正）
                        if st.button("建", key=f"b_{x}_{y}"):
                            if state['money'] >= 50: # 資金チェック追加
                                # 周囲の敵を検索して属性を決定
                                target_enemy = next((e for e in state['enemies'] if abs(e['x'] - x) <= 1 and abs(e['y'] - y) <= 1), None)
                                attr = get_counter_attr(target_enemy['attr']) if target_enemy else "fire"
                                
                                # HPを含めて保存
                                state['towers'][(x, y)] = {'attr': attr, 'hp': 10} 
                                state['money'] -= 50
                                st.rerun()
                    else:
                        # 塔がある場合はボタンを出さない、あるいは別のUIにする
                        st.empty() 
                else:
                    # 道の部分は建設不可なので何もしない
                    st.empty()
# --- ゲーム進行処理 ---
def game_logic():
    state = st.session_state.game_state
    path = get_path(state['stage'])
    
    # 1. 射程によるタワーからの攻撃
    range_bonus = state['stage'] // 3 
    for pos, tower in state['towers'].items():
        for e in state['enemies']:
            if abs(pos[0] - e['x']) <= (1 + range_bonus) and abs(pos[1] - e['y']) <= (1 + range_bonus):
                damage = 2 if ATTRIBUTES.get(tower['attr']) == e['attr'] else 1
                e['hp'] -= damage

    # 2. 敵の移動とタワーへのダメージ
    for e in state['enemies']:
        e['x'] += 1
        if e['x'] < 6:
            e['y'] = path[e['x']]
            # 【重要】敵がタワーと同じ座標にいたらダメージ
            if (e['x'], e['y']) in state['towers']:
                state['towers'][(e['x'], e['y'])]['hp'] -= 2  # ダメージ量
                # タワー破壊判定
                if state['towers'][(e['x'], e['y'])]['hp'] <= 0:
                    del state['towers'][(e['x'], e['y'])]
        elif e['x'] >= 6:
            state['tower_hp'] -= 2
            e['x'] = 0

    # 3. 敵の撃破判定と報酬
    state['enemies'] = [e for e in state['enemies'] if e['hp'] > 0]
    
    # 4. 全滅・ステージ進行判定
    if len(state['enemies']) == 0:
        state['money'] += 100
        reset_game_state(state['stage'] + 1)
    
    # 5. ゲームオーバー判定
    if state['tower_hp'] <= 0:
        state['game_over'] = True

# --- メイン画面 ---
st.title("🏰 Magic Defense")
st.write(f"Gold: {state['money']}")

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
