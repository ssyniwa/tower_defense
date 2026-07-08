import streamlit as st
import time

# 設定
GRID_SIZE = 6
st.set_page_config(page_title="Magic TD", layout="centered")

# 初期化
if 'game_state' not in st.session_state:
    st.session_state.game_state = {
        'tower_hp': 10,
        'enemies': [{'x': 0, 'y': 3, 'hp': 5}], # 敵の初期位置
        'towers': {}, # {(x, y): {'level': 1}}
        'running': True
    }

def draw_grid():
    """フェーズ1: グリッド描画"""
    state = st.session_state.game_state
    
    for y in range(GRID_SIZE):
        cols = st.columns(GRID_SIZE)
        for x in range(GRID_SIZE):
            cell_content = "🟩" # 道
            if (x, y) in state['towers']:
                cell_content = "🏰"
            for e in state['enemies']:
                if e['x'] == x and e['y'] == y:
                    cell_content = f"👿({e['hp']})"
            
            with cols[x]:
                if st.button(cell_content, key=f"{x}_{y}"):
                    state['towers'][(x, y)] = {'level': 1}

def update_game():
    """フェーズ2 & 3: 移動・攻撃ロジック"""
    state = st.session_state.game_state
    
    # 敵の移動 (フェーズ2)
    for e in state['enemies']:
        e['x'] += 1
        if e['x'] >= GRID_SIZE:
            state['tower_hp'] -= 1
            e['x'] = 0
            
    # タワー攻撃 (フェーズ3)
    for pos, tower in state['towers'].items():
        for e in state['enemies']:
            # 射程(隣接)内にいればダメージ
            if abs(pos[0] - e['x']) <= 1 and abs(pos[1] - e['y']) <= 1:
                e['hp'] -= 1
    
    # 撃破判定
    state['enemies'] = [e for e in state['enemies'] if e['hp'] > 0]

# メイン画面表示
st.title("Magic Defense")
st.write(f"Castle HP: {st.session_state.game_state['tower_hp']}")

if st.session_state.game_state['tower_hp'] > 0:
    draw_grid()
    update_game()
    time.sleep(1) # ゲーム速度調整
    st.rerun()
else:
    st.error("GAME OVER! 城が崩壊しました...")
    if st.button("リトライ"):
        del st.session_state.game_state
        st.rerun()
