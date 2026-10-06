from flask import Flask, render_template, jsonify, request
import random

app = Flask(__name__)

BOARD_SIZE = 20
WIN_LENGTH = 5

game = {
    "board": [""] * (BOARD_SIZE * BOARD_SIZE),
    "current_player": "X",
    "winner": None,
    "players": {}, # player_id -> X / O
}

PATTERNS = {
    "WIN5": 1000000,
    "OPEN4": 100000,
    "BLOCKED4": 10000,
    "OPEN3": 10000,
    "BLOCKED3": 1000,
    "OPEN2": 100,
}

def evaluate_line(line, symbol):
    opp = "O" if symbol == "X" else "X"
    count_sym = line.count(symbol)
    count_opp = line.count(opp)
    
    if count_sym > 0 and count_opp > 0:
        return 0
    
    if count_sym == 5: return PATTERNS["WIN5"]
    if count_opp == 5: return -PATTERNS["WIN5"]
    
    score = 0
    if count_sym > 0:
        score += 10 ** count_sym
    if count_opp > 0:
        score -= (10 ** count_opp) * 1.2
        
    return score

def evaluate_board_master(board, bot_symbol):
    score = 0
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            for dr, dc in directions:
                if 0 <= r + 4*dr < BOARD_SIZE and 0 <= c + 4*dc < BOARD_SIZE:
                    line = [board[(r + i*dr) * BOARD_SIZE + (c + i*dc)] for i in range(5)]
                    score += evaluate_line(line, bot_symbol)
    return score

def get_smart_candidates(board, radius=1):
    candidates = set()
    has_moves = False
    for pos, val in enumerate(board):
        if val != "":
            has_moves = True
            r, c = pos // BOARD_SIZE, pos % BOARD_SIZE
            for dr in range(-radius, radius + 1):
                for dc in range(-radius, radius + 1):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                        npos = nr * BOARD_SIZE + nc
                        if board[npos] == "":
                            candidates.add(npos)
    if not has_moves:
        return [BOARD_SIZE * (BOARD_SIZE // 2) + BOARD_SIZE // 2]
    return list(candidates)

def minimax_master(board, depth, alpha, beta, is_max, bot_symbol):
    candidates = get_smart_candidates(board, radius=1)
    if depth == 0 or not candidates:
        return evaluate_board_master(board, bot_symbol), None

    best_move = candidates[0]
    opp_symbol = "O" if bot_symbol == "X" else "X"

    if is_max:
        max_eval = -float('inf')
        for move in candidates:
            board[move] = bot_symbol
            if check_winner(board, move) == bot_symbol:
                board[move] = ""
                return PATTERNS["WIN5"], move
            
            eval_score, _ = minimax_master(board, depth - 1, alpha, beta, False, bot_symbol)
            board[move] = ""
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in candidates:
            board[move] = opp_symbol
            if check_winner(board, move) == opp_symbol:
                board[move] = ""
                return -PATTERNS["WIN5"], move
            
            eval_score, _ = minimax_master(board, depth - 1, alpha, beta, True, bot_symbol)
            board[move] = ""
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_move

def make_bot_move(difficulty="master", bot_symbol="O"):
    candidates = get_smart_candidates(game["board"], radius=1)
    if not candidates or game["winner"]:
        return

    selected_move = None
    if difficulty == "novice":
        if random.random() < 0.6:
            selected_move = random.choice(candidates)
        else:
            _, selected_move = minimax_master(game["board"], depth=1, alpha=-float('inf'), beta=float('inf'), is_max=True, bot_symbol=bot_symbol)
    elif difficulty == "easy":
        _, selected_move = minimax_master(game["board"], depth=1, alpha=-float('inf'), beta=float('inf'), is_max=True, bot_symbol=bot_symbol)
    elif difficulty == "medium":
        _, selected_move = minimax_master(game["board"], depth=2, alpha=-float('inf'), beta=float('inf'), is_max=True, bot_symbol=bot_symbol)
    elif difficulty == "master":
        _, selected_move = minimax_master(game["board"], depth=3, alpha=-float('inf'), beta=float('inf'), is_max=True, bot_symbol=bot_symbol)

    if selected_move is not None:
        game["board"][selected_move] = bot_symbol
        winner = check_winner(game["board"], selected_move)
        if winner:
            game["winner"] = winner
        elif all(game["board"]):
            game["winner"] = "DRAW"
        else:
            game["current_player"] = "X" if bot_symbol == "O" else "O"

def check_winner(board, position):
    player = board[position]
    if not player:
        return None

    row = position // BOARD_SIZE
    col = position % BOARD_SIZE
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

    for dr, dc in directions:
        count = 1
        r, c = row + dr, col + dc
        while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r * BOARD_SIZE + c] == player:
            count += 1
            r += dr
            c += dc

        r, c = row - dr, col - dc
        while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r * BOARD_SIZE + c] == player:
            count += 1
            r -= dr
            c -= dc

        if count >= WIN_LENGTH:
            return player

    return None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/join", methods=["POST"])
def join():
    data = request.json
    player_id = data.get("player_id")
    requested_symbol = data.get("symbol", "X") # Mặc định chọn X nếu không truyền

    if player_id in game["players"]:
        return jsonify({
            "success": True,
            "symbol": game["players"][player_id]
        })

    if requested_symbol in ["X", "O"]:
        game["players"][player_id] = requested_symbol
        return jsonify({
            "success": True,
            "symbol": requested_symbol
        })

    return jsonify({
        "success": False,
        "message": "Vui lòng chọn X hoặc O"
    })

@app.route("/state")
def state():
    return jsonify({
        "board": game["board"],
        "current_player": game["current_player"],
        "winner": game["winner"],
        "players": game["players"],
    })

@app.route("/move", methods=["POST"])
def move():
    data = request.json
    player_id = data.get("player_id")
    position = data.get("position")
    difficulty = data.get("difficulty", "master")
    mode = data.get("mode", "pve")

    if player_id not in game["players"]:
        return jsonify({"success": False, "message": "Bạn chưa tham gia game"})

    player = game["players"][player_id]

    if game["winner"]:
        return jsonify({"success": False, "message": "Game đã kết thúc"})

    if player != game["current_player"]:
        return jsonify({"success": False, "message": "Chưa tới lượt bạn"})

    if not isinstance(position, int) or not (0 <= position < BOARD_SIZE * BOARD_SIZE):
        return jsonify({"success": False, "message": "Position không hợp lệ"})

    if game["board"][position]:
        return jsonify({"success": False, "message": "Ô này đã được đánh"})

    # Đánh nước đi của người chơi
    game["board"][position] = player

    winner = check_winner(game["board"], position)
    if winner:
        game["winner"] = winner
    elif all(game["board"]):
        game["winner"] = "DRAW"
    else:
        # Chuyển lượt
        game["current_player"] = "O" if player == "X" else "X"
        
        # Nếu đang ở chế độ đánh với máy (PvE)
        if mode == "pve" and not game["winner"]:
            bot_symbol = "O" if player == "X" else "X"
            make_bot_move(difficulty=difficulty, bot_symbol=bot_symbol)

    return jsonify({"success": True})

@app.route("/restart", methods=["POST"])
def restart():
    game["board"] = [""] * (BOARD_SIZE * BOARD_SIZE)
    game["current_player"] = "X"
    game["winner"] = None
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3651, debug=False)