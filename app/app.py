from flask import Flask, render_template, request, jsonify
from utils import load_data, create_queue
from database import myMySQL

app = Flask(__name__)
# JSONで日本語を扱えるようにする
app.config["JSON_AS_ASCII"] = False

class Quiz:
    view_mode = False # クイズモードか確認モードのフラグ（False:クイズモード）
    # データベースへの接続に使うパラメータ
    config = {
      'user': 'root',
      'password': 'root',
      'port': 3306,
      'host': 'mysql', # DockerのMySQLイメージでビルドしたコンテナに接続する場合
      'database': 'railway',
      'charset': 'utf8',
    }

    # コンストラクタ
    def __init__(self):
        self.count = 0 # 問題番号
        self.db = myMySQL(**self.config) # データベースのインスタンスを取得
        # 会社名でソートして会社名と英語名のリストを取得する
        stmt = "SELECT company, eng_company from routes ORDER BY company"
        companies_data = self.db.query(stmt)
        # 日本語名で会社名データを保存（会社名は重複しているので一度setにしてlistに戻す）
        self.companies = list(set([d[0] for d in companies_data]))
        # 会社名の日本語名と英語名を対応させる辞書を作る
        self.dic_companies_ja_to_eng = {d[0]:d[1] for d in companies_data}
        self.dic_companies_eng_to_ja = {d[1]:d[0] for d in companies_data}
        # current_...は日本語名で保持する
        # 最初のデータをデフォルトとして持っておく
        self.current_company = self.companies[0]
        # current_companyに対する路線名データをセットする（ここでself.routesがセットされる）
        self.set_railway_routes()
        # 同様に最初のものをデフォルトにする
        self.current_route = self.routes[0]

    # 選択している会社を変更
    def set_company(self, company_name):
        if company_name in self.companies:
            # データの中にあればそれをセットする
            self.current_company = company_name
        elif company_name in self.dic_companies_eng_to_ja:
            # 英語名の辞書にキーがある場合それで日本語に変換して格納する
            self.current_company = self.dic_companies_eng_to_ja[company_name]
        else:
            print("(Quiz::set_company) : inappropriate value")
            quit()

    # 現在の会社に対する路線名一覧情報を取得し保存
    def set_railway_routes(self):
        # 路線データからcompanyがcurrent_companyのデータを取ってくる
        stmt = "SELECT name, eng_name from routes WHERE company = %s ORDER BY name"
        routes_data = self.db.query(stmt, self.current_company)
        # 路線リストを作って保存
        self.routes = [d[0] for d in routes_data]
        # 日本語の路線名から英語名に変換する辞書
        self.dic_routes_ja_to_eng = {d[0]:d[1] for d in routes_data}
        self.dic_routes_eng_to_ja = {d[1]:d[0] for d in routes_data}
    def get_companies(self):
        return [self.companies, self.dic_companies_ja_to_eng, self.dic_companies_eng_to_ja]
    def get_railway_routes(self):
        return [self.routes, self.dic_routes_ja_to_eng, self.dic_routes_eng_to_ja]

    # クイズが開始されるとき呼び出されて出題の設定をする
    def set_params(self, company, route, updown=True, view_mode=False):
        self.count = 0 # 問題番号
        self.correct_num = 0 # 正解数
        self.updown = updown # 上り・下りのスイッチ
        self.view_mode = view_mode # 正解確認モードのスイッチ
        self.set_company(company) # 企業を設定
        # 選ばれているものと実際には違う辞書になっていることがあるので送信時のデータで一度更新する
        self.set_railway_routes()

        if route in self.routes:
            # セットしたいデータが路線リストにあればセット
            self.current_route = route
        elif route in self.dic_routes_eng_to_ja:
            # 英語名で送られてきたら直す
            self.current_route = self.dic_routes_eng_to_ja[route]
        else:
            print("(Quiz::set_params) : inappropriate value (current route set)")
            quit()
        self.previous_answer = None # 前の問題の答えを保存しておく変数
        self.previous_kilopost = 0.0 # 前の問題の答え（駅）のキロポストを保存して駅間距離の計算に使う

        # 駅データから企業と路線名が一致するデータをキロポストでソートして持ってくる. updownで昇順降順を切り替える
        stmt = "SELECT * FROM stations WHERE company = %s and route_name = %s ORDER BY kilopost "
        stmt += "ASC" if self.updown else "DESC"
        data = self.db.query(stmt, self.current_company, self.current_route)
        # データをキューに入れてセットする
        self.data = create_queue(data)

    # 次の問題をpop
    def pop_question(self):
        return self.data.popleft()

    # 空かどうかを取得
    def question_empty(self):
        return len(self.data) == 0

    # 現在の問題番号を取得
    def get_question_num(self):
        return self.question_num

    # 次の問題を出題する
    def display_next_question(self):
        # データを取ってくる
        data = self.pop_question()
        # 問題番号を増やす
        self.count += 1
        # 個別の変数に展開
        company, route_name, number, name, kilopost, connect_routes, prefecture, municipality, ward, desc = list(data)
        # 答えは駅名
        answer = name
        # 問題文
        # 一問目以外なら前の駅があるはずなのでそれを使って問題文を作成. また駅間距離も計算（方向が両方ありえるので絶対値計算）
        # 一問目の場合問題文とキロポストを特別に指定
        question_text = ''
        if self.previous_answer != None:
            question_text += self.previous_answer
            question_text += '駅->？駅'
            distance = round(abs(kilopost - self.previous_kilopost),1)
        else:
            question_text += '起点：？駅'
            distance = '-'

        # 前の問題の答えとキロポストを更新
        self.previous_answer = name
        self.previous_kilopost = kilopost
        desc = desc if desc != None else "" # 説明文. なければ空文字列
        # 接続路線をリストに変換（データは半角スペースで区切られている）. なければ空リスト
        connect_routes = connect_routes.split() if connect_routes != None else []
        # 駅情報をセット
        station_address = ""
        station_address += prefecture if prefecture != None else ""
        station_address += municipality if municipality != None else ""
        station_address += ward if ward != None else ""
        # 駅データを辞書にしてセット
        station_info = {'駅番号': (number if number != None else "なし"), '所在地': station_address, 'キロポスト': kilopost, '駅間距離': distance}
        # 埋め込むデータをまとめる
        prop = {'question_text': question_text, 'answer': answer, 'question_num': self.count, 'viewmode':self.view_mode, 'description': desc, 'connect_routes':connect_routes, 'station_info': station_info}
        # Jinja2のテンプレートを返す
        return render_template('quiz.html', **prop)

    # 正解数を管理
    def add_correct_num(self, request=None):
        if self.view_mode:
            # 答え閲覧モードなら正解数は無視する
            return
        else:
            # クイズモードなら, 送られてきた正否の文字列を取得して正解なら加算
            correctness = request.form['correctness']
            if correctness == "正解":
                self.correct_num += 1

    # 結果画面で使う結果データを作る. 基本的には埋め込む文字列を作って返すことにする
    def get_results(self):
        if self.view_mode:
            return None
        results = []
        results.append(f"{quizapp.correct_num}問正解！")
        return results

quizapp = Quiz()
# この辺多分めちゃくちゃ無駄なのでそのうちなんとかしたい
companies, dic_companies_ja_to_eng, dic_companies_eng_to_ja = quizapp.get_companies()
routes, dic_routes_ja_to_eng, dic_routes_eng_to_ja = quizapp.get_railway_routes()

# ルートへのアクセス（デフォルト画面）
@app.route('/')
def home():
    prop = {'companies':companies, 'dic_companies_ja_to_eng':dic_companies_ja_to_eng, 'routes':routes, 'dic_routes_ja_to_eng':dic_routes_ja_to_eng,}
    return render_template('index.html', **prop)

# 企業名を選択した際に路線名をセットするためのURL
@app.route('/get_routes', methods=['POST'])
def get_routes_as_json():
    if request.method == 'POST':
        # valueを日本語に直す
        company = dic_companies_eng_to_ja.get(request.form['company_select'], None)
        if company != None:
            # 存在すればセットして路線リストを更新する
            quizapp.set_company(company)
            quizapp.set_railway_routes()
        routes, dic_routes_ja_to_eng, dic_routes_eng_to_ja = quizapp.get_railway_routes()
        # JSON形式で辞書を返す
        return jsonify(dic_routes_eng_to_ja)

# 開始直後
@app.route('/start', methods=['POST'])
def start():
    if request.method == 'POST':
        updown_dic = {"down": True, "up": False}
        onoff_dic = {"on": True, "off": False}
        updown = updown_dic[request.form['updown']]
        view_mode = onoff_dic[request.form['viewflag']]
        company_id = request.form['company_select']
        route_id = request.form['route_select']
        quizapp.set_params(company=company_id, route=route_id, updown=updown, view_mode=view_mode)
        return quizapp.display_next_question()

@app.route('/quiz', methods=['POST'])
def quiz():
    if request.method == 'POST':
        quizapp.add_correct_num(request=request)
        if quizapp.question_empty():
            results = quizapp.get_results()
            return render_template('result.html', results=results)
        else:
            return quizapp.display_next_question()

if __name__ == "__main__":
    app.run(debug=False)
