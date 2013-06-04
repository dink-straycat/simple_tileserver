simple_tileserver
=================

Apache, mod_tile不要のタイルサーバです。DB環境とmapnikは必要。

検証環境はLinux Mint 14ですが、たぶん最新のUbuntuでも動くんじゃないかな。

## タイルの生成まで

まず、gitリポジトリを複製。

    git clone https://github.com/dink-straycat/simple_tileserver.git
    git clone https://github.com/openstreetmap/mapnik-stylesheets.git

海岸線のshapeファイルを拾ってくる。それなりに大きくて時間がかかります。

    cd mapnik-stylesheet
    ./get-coastlines.sh

お好きなOpenStreetMapのデータを持ってきます。以下はBBbike.orgからTokyoのデータを持ってくる手順。だいたい20MB程度。

    wget http://download.bbbike.org/osm/bbbike/Tokyo/Tokyo.osm.gz

PostGISのインストール。インストール後に自動的に起動します。

    sudo apt-get install postgresql-9.1-postgis osm2pgsql

osm2pgsqlをインストール。

    sudo add-apt-repository ppa:kakrueger/openstreetmap
    sudo apt-get update
    sudo apt-get install osm2pgsql

mapnikのインストール。

    sudo add-apt-repository ppa:mapnik/v2.1.0
    sudo apt-get update
    sudo apt-get install libmapnik mapnik-utils python-mapnik

DBの作成(osm2pgsqlインストール時に自動的に作られてるかも)。$USERは自分のユーザ名に置き換えて...

    sudo su - postgres
    createuser $USER --no-createdb --no-createrole --no-superuser --no-password
    createdb --owner=$USER gis
    psql -d gis -f /usr/share/postgresql/9.1/contrib/postgis-1.5/postgis.sql
    psql -d gis -f /usr/share/postgresql/9.1/contrib/postgis-1.5/spatial_ref_sys.sql
    psql -d gis -f /usr/share/postgresql/9.1/contrib/postgis_comments.sql
    psql -d gis -c "ALTER TABLE geometry_columns OWNER TO $USER;"
    psql -d gis -c "ALTER TABLE spatial_ref_sys OWNER TO $USER;"
    psql -d gis -c "ALTER VIEW geography_columns OWNER TO $USER;"
    exit

データを投入。

    osm2pgsql Tokyo.osm.gz

設定ファイル作成。

    ./generate_xml.py --dbname gis --user $USER --accept-none

以上で設定は完了です。サーバの起動は次の手順で。

    cd ../simple_tileserver
    ./simple_tileserver.py

http://localhost:8080/ にアクセスすると、OpenLayersを使ってタイルを表示します。キャッシュは作ってないので毎回タイルが生成されます。初期表示する場所などはmap_template.htmlをいじってください。

## 日本語フォントの設定

Takao PGothicを使うには、次のコマンドでmapnikがフォントを読めるようにリンクを張ってください。

    sudo ln -s /etc/alternatives/fonts-japanese-gothic.ttf /usr/share/fonts/truetype/ttf-dejavu/

上記設定の上、mapnik-stylesheetsの中のinc/fontset-settings.xmlに以下が最優先になるよう記述してください。

    <Font face-name="TakaoPGothic Regular" /> 

