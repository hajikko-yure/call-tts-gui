# Character Call TTS

## 概要
VOICEVOXとVoicemeeterを使用して、LINE通話などでずんだもんの声で通話するプログラムです。

## 動作環境
- **Python 3.10以上**
- **VOICEVOX**: 音声合成用です。[VOICEVOX公式サイト](https://voicevox.hiroshiba.jp/)  からダウンロードできます。 
（デフォルトパス: `C:\Program Files\VOICEVOX\VOICEVOX.exe`）。

- **Voicemeeter**: オーディオルーティング用です。[Voicemeeter公式サイト](https://vb-audio.com/Voicemeeter/index.htm)からダウンロードできます。  （デフォルトパス: `C:\Program Files (x86)\VB\Voicemeeter\voicemeeter_x64.exe`）。

## インストール
1. このリポジトリをクローンまたはダウンロードします。
2. 依存関係をインストールします:
    ```bash
    pip install -r requirements.txt
    ```

## 使い方
1. アプリケーションを実行します:
    ```bash
    python main.py
    ```
2. **デバイス選択**: 出力デバイスを選択します（Voicemeeter Input）。
3. **キャラクター選択**: Voicevoxのキャラクターを選択します。
4. **発言**: 下部のバーに入力し、Enterキーを押すか、紙飛行機アイコンをクリックします。
5. **効果音**: `+` ボタンでWAVファイルを追加し、ボタンをクリックして再生します。

## 設定
`config.json` を編集してデフォルト設定を変更できます:
```json
{
    "voicevox_url": "http://127.0.0.1:50021",
    "default_speed": 1.0,
    "default_volume": 1.0,
    "default_pitch": 0.0,
    "default_speaker_name": "ずんだもん",
    "default_speaker_style": "ノーマル"
}
```

## クレジット
- **Voicevox**: [https://voicevox.hiroshiba.jp/](https://voicevox.hiroshiba.jp/)
- **Character Call TTS 開発者**: はじっこゆーれー

## ライセンス
MIT License
