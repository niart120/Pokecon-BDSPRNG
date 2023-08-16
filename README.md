# Pokecon-BDSPRNG
 
## What's this?
Nintendo Switchの自動操作ツールの一つである[Poke-Controller](https://github.com/Moi-poke/Poke-Controller-Modified)で動くコードを纏めたものです.

現在以下のコードを纏めています.
- `idrng.py` 
	- 直近に目的のIDが見つかるまで, ゴンベの瞬きから自動的にSeedを特定してSeed厳選を行います.
	- メニュー画面でBDSPのソフトにカーソルが合っている状態で実行してください.
	- id調整を行う用のアカウントを新しく作成した上で, ゲーム起動時にそのアカウントにカーソルがあっている必要があります.

また, `target_g7tid_list` または `target_tidsid_list` のいずれかのリストに目的のIDを格納してください.

## 使い方
**`bdsprnglib` フォルダ** と, 利用したいソースコードを纏めて `Commands\PythonCommands` 配下に配置してください.

## ライセンス
このリポジトリに含まれるコードは全てMITライセンスに準拠します. 

## 依存ライブラリ
[PokemonBDSPRNGLibrary-python](https://github.com/niart120/PokemonBDSPRNGLibrary-python)