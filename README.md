# Pokecon-BDSPRNG
 
## What's this?
Nintendo Switchの自動操作ツールの一つである[Poke-Controller](https://github.com/Moi-poke/Poke-Controller-Modified)で動くコードを纏めたものです.

現在以下のコードを纏めています.
- `idrng.py` 
	- **ゲームの起動から基準Seed厳選, ID検索, 乱数消費, ID決定までの操作を自動で実行します.**
	- `target_g7tid_list` または `target_tidsid_list` のいずれかに目的のIDを格納して実行します.
	- 名前入力画面まで到達したのち, ホーム画面に戻って自動操作を終了します. 任意の名前を入力してストーリーを開始し, 目的のIDが得られているかを確認してください.
	- メニュー画面でBDSPのソフトにカーソルが合っている状態で実行してください.
	- id調整を行う用のアカウントを新しく作成した上で, ゲーム起動時にそのアカウントにカーソルがあっている必要があります.
	- _注意:名前入力後の博士からの確認画面は必ず"はい"を選択してください._


## 使い方
**`bdsprnglib` フォルダ** と, 利用したいソースコードを纏めて `Commands\PythonCommands` 配下に配置してください.

## ライセンス
このリポジトリに含まれるコードは全てMITライセンスに準拠します. 

## 依存ライブラリ
[PokemonBDSPRNGLibrary-python](https://github.com/niart120/PokemonBDSPRNGLibrary-python)