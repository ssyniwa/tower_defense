import streamlit as st
import time
import json

# --- 設定 ---
GRID_SIZE = 8 # 少し広くしました
CELL_SIZE_PX = 40 # スマホで押しやすいサイズ（約40px）
st.set_page_config(page_title="Magic TD", layout="centered")

# --- 初期化 ---
if 'game_state' not in st.session_state:
    st.session_state.game_state = {
        'tower_hp': 20,
        'enemies': [{'id': 1, 'x': 0, 'y': 4, 'hp': 5}], # IDを追加管理
        'towers': {}, # {(x, y): {'type': 'magic'}}
        'money': 50, # MVPに含めなかったが画像表示のために資金を追加
        'tick': 0, # アニメーション用のカウンター
        'running': True
    }

# --- 外部CSS定義（HTMLコンポーネント内で使用） ---
# クリック時の青枠を消すなど、ゲームっぽい見た目にする
GAME_STYLE = """
<style>
    .game-grid {
        display: grid;
        grid-template-columns: repeat(8, 1fr);
        gap: 2px;
        max-width: 400px; /* スマホ表示を考慮 */
        margin: auto;
    }
    .cell {
        aspect-ratio: 1 / 1;
        background-color: #e0f2f1; /* 薄い緑 */
        border: 1px solid #b2dfdb;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px; /* 絵文字のサイズ */
        cursor: pointer;
        user-select: none;
        transition: background-color 0.1s;
    }
    .cell:active {
        background-color: #b2dfdb;
    }
    /* パス（道）の色 */
    .cell-path {
        background-color: #fff9c4; 
    }
</style>
"""

def draw_grid_html():
    """
    フェーズ1改良: HTML/JSを使ってボタンを描画・更新する。
    Streamlitのボタンリロードによるチラつきを抑える。
    """
    state = st.session_state.game_state
    
    # 現在のグリッド状態をHTMLの文字列として構築
    grid_html = GAME_STYLE + '<div class="game-grid">'
    
    # 固定のパス（簡易的にy=4の列を通ることにする）
    path_y = 4
    
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            # セルの基本クラス
            cell_class = "cell"
            content = ""
            
            # 1. 道の判定
            if y == path_y:
                cell_class += " cell-path"
            
            # 2. タワーの描画 (画像/絵文字)
            if (x, y) in state['towers']:
                content = "🏰" # タワー画像
                
            # 3. 敵の描画 (画像/絵文字) - 重なった場合は敵を優先
            # チカチカさせるため、tickの偶奇で画像を変える（アニメーションの基本）
            for e in state['enemies']:
                if e['x'] == x and e['y'] == y:
                    # HPによって色（絵文字）を変える
                    if e['hp'] > 3:
                        content = "👿" if state['tick'] % 2 == 0 else "👺"
                    else:
                        content = "👾" # 瀕死
            
            # 各セルをdiv要素として作成。クリックイベントをstreamlit側に送る細工をする
            # idを "x-y" の形式にする
            grid_html += f'<div class="cell {cell_class}" id="{x}-{y}" onclick="parent.postMessage(this.id, \'*\')">{content}</div>'
            
    grid_html += '</div>'

    # StreamlitでHTMLを表示。これがゲーム画面になる
    # components.html は高さ自動調整が難しいため、グリッドサイズから固定値を計算
    component_height = GRID_SIZE * (CELL_SIZE_PX + 4) 
    clicked_cell = st.components.v1.html(grid_html, height=component_height, scrolling=False)
    
    # JavaScriptからメッセージ（クリックされたID）が送られてきたら処理する
    # st.components.v1.html は最後に評価された値を返す性質を利用する
    if clicked_cell:
        try:
            x_str, y_str = clicked_cell.split('-')
            pos = (int(x_str), int(y_str))
            
            # タワー建設ロジック（道以外、所持金50以上）
            if pos[1] == path_y:
                st.warning("そこは道です！")
            elif pos in state['towers']:
                st.warning("既に塔があります")
            elif state['money'] >= 50:
                state['towers'][pos] = {'level': 1}
                state['money'] -= 50
                st.rerun() # 即座に反映
            else:
                st.warning("資金不足です (Need 50G)")
        except ValueError:
            pass

def update_game():
    """フェーズ2 & 3: 移動・攻撃ロジック（変更なし）"""
    state = st.session_state.game_state
    path_y = 4 # 固定パス
    
    # アニメーション用カウンターを進める
    state['tick'] += 1
    
    # 敵の移動
    enemies_to_remove = []
    for e in state['enemies']:
        e['x'] += 1
        # ゴール判定
        if e['x'] >= GRID_SIZE:
            state['tower_hp'] -= 1
            enemies_to_remove.append(e['id'])
            
    # ゴールした敵を削除
    state['enemies'] = [e for e in state['enemies'] if e['id'] not in enemies_to_remove]
            
    # タワー攻撃
    for pos, tower in state['towers'].items():
        target = None
        # 単純な射程チェック（隣接8マス）
        for e in state['enemies']:
            if abs(pos[0] - e['x']) <= 1 and abs(pos[1] - e['y']) <= 1:
                target = e
                break # 1体攻撃したら終了
        
        if target:
            target['hp'] -= 2 # タワー攻撃力
            # 撃破時の処理
            if target['hp'] <= 0:
                state['enemies'] = [e for e in state['enemies'] if e['id'] != target['id']]
                state['money'] += 20 # 撃破報酬
    
    # 新しい敵のスポーン（テスト用、一定確率）
    if state['tick'] % 5 == 0: # 5フレームごとに生成
        new_id = state['tick']
        state['enemies'].append({'id': new_id, 'x': 0, 'y': path_y, 'hp': 5})

# --- メイン画面表示 ---
st.title("🏰 Magic Defense Online")

# ステータス表示エリア
col1, col2, col3 = st.columns(3)
col1.metric("Castle HP", f"{st.session_state.game_state['tower_hp']} / 20", delta_color="normal")
col2.metric("Gold", f"{st.session_state.game_state['money']} G")
col3.metric("Enemies", len(st.session_state.game_state['enemies']))

if st.session_state.game_state['tower_hp'] > 0:
    # HTMLベースのグリッド描画関数を呼び出し
    draw_grid_html()
    update_game()
    
    # ゲーム速度調整（HTML使用時は少し短くてもスムーズに見える）
    time.sleep(0.5) 
    st.rerun()
else:
    st.error("GAME OVER! 城が陥落しました...")
    if st.button("リトライ"):
        del st.session_state.game_state
        st.rerun()
