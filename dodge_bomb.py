import math
import os
import pygame as pg
import random
import sys
import time


WIDTH, HEIGHT = 1100, 650
DELTA = {pg.K_UP: (0, -5), pg.K_DOWN: (0, +5), pg.K_LEFT: (-5, 0), pg.K_RIGHT: (5, 0),}
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(rct: pg.Rect) -> tuple[bool, bool]:
    """
    引数で与えられたRectが画面内or画面外を判定する関数
    引数：こうかとんRactまたは爆弾Rect
    戻り値：横方向、縦方向判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if rct.left < 0 or WIDTH < rct.right:
        yoko = False
    if rct.top < 0 or HEIGHT < rct.bottom:
        tate = False
    return yoko, tate


def gameover(screen: pg.Surface) -> None:
    """
    ゲームオーバー画面を表示する関数
    引数：screen(画面Surface)
    """
    bg_img = pg.Surface((WIDTH,HEIGHT))
    pg.draw.rect(bg_img,(0,0,0),(0,0,WIDTH,HEIGHT))

    bg_img.set_alpha(150)

    fonto = pg.font.Font(None,80)
    txt = fonto.render("Game Over", True ,(255, 255, 255))
    txt_rct=txt.get_rect()
    txt_rct.center = WIDTH // 2, HEIGHT // 2
    bg_img.blit(txt, txt_rct)

    kk_img1 = pg.image.load("fig/8.png")
    kk_rct1 = kk_img1.get_rect()
    kk_rct1.center = WIDTH // 2 - 200, HEIGHT // 2
    bg_img.blit(kk_img1, kk_rct1)
    kk_rct2 = kk_img1.get_rect()
    kk_rct2.center = WIDTH // 2 + 200, HEIGHT // 2
    bg_img.blit(kk_img1, kk_rct2)

    screen.blit(bg_img, [0, 0])
    
    pg.display.update()
    time.sleep(5)


def init_bb_imgs() -> tuple[list[pg.Surface], list[int]]:
    """
    サイズの異なる爆弾Surfaceを要素とするリストと、加速度リストを返す関数
    """
    bb_imgs = []
    bb_accs = [a for a in range(1, 11)]  # 加速度のリスト(1〜10)
    
    for r in range(1, 11):  # 1〜10の10段階でループ 
        # サイズを拡大させた空のSurfaceを作る 
        bb_img = pg.Surface((20*r, 20*r))
        # 拡大したSurfaceに合わせて赤い円を描画する
        pg.draw.circle(bb_img, (255, 0, 0), (10*r, 10*r), 10*r)
        # 背景の黒色を透明にする 
        bb_img.set_colorkey((0, 0, 0))
        # リストに追加
        bb_imgs.append(bb_img)
        
    return bb_imgs, bb_accs  # 2つのリストをタプルとして返す


def get_kk_imgs() -> dict[tuple[int, int], pg.Surface]:
    """
    移動量のタプルをキー、向きに対応したこうかとん画像を値とする辞書を返す関数
    """
    # 基本のこうかとんをロードして少し縮小
    kk_img = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    kk_img_f = pg.transform.flip(kk_img, True, False)
    
    # 移動量のタプルをキーとして、rotozoomで回転させた画像を辞書に登録する
    kk_imgs = {
        (0, 0): kk_img_f,  # 停止中（右向きをデフォルトにする）
        (+5, 0): kk_img_f, # 右
        (+5, -5): pg.transform.rotozoom(kk_img_f, 45, 1.0),   # 右上
        (0, -5): pg.transform.rotozoom(kk_img_f, 90, 1.0),    # 上
        (-5, -5): pg.transform.rotozoom(kk_img, -45, 1.0),    # 左上 (左向きを時計回りに45度)
        (-5, 0): kk_img,   # 左
        (-5, +5): pg.transform.rotozoom(kk_img, 45, 1.0),     # 左下 (左向きを反時計回りに45度)
        (0, +5): pg.transform.rotozoom(kk_img_f, -90, 1.0),   # 下
        (+5, +5): pg.transform.rotozoom(kk_img_f, -45, 1.0),  # 右下
    }
    return kk_imgs


def calc_orientation(org: pg.Rect, dst: pg.Rect, current_xy: tuple[float, float]) -> tuple[float, float]:
    """
    爆弾からこうかとんへ向かう方向のベクトルを計算する関数
    引数1 org: 爆弾のRect
    引数2 dst: こうかとんのRect
    引数3 current_xy: 現在の爆弾の速度ベクトル
    戻り値: 正規化後方向ベクトル or 計算前の方向ベクトル
    """
    # 1. 差ベクトルを求める (こうかとんの座標 - 爆弾の座標)
    diff_x = dst.centerx - org.centerx
    diff_y = dst.centery - org.centery

    # 2. 差ベクトルのノルム(距離)を計算する
    norm = math.sqrt(diff_x**2 + diff_y**2)

    # 3. 距離が300未満だったら、慣性として計算前の方向(current_xy)に移動させる
    if norm < 300:
        return current_xy

    # 4. 差ベクトルのノルムが√50になるように正規化する
    new_vx = (diff_x / norm) * math.sqrt(50)
    new_vy = (diff_y / norm) * math.sqrt(50)

    return new_vx, new_vy


def main():
    pg.display.set_caption("逃げろ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")   
    # 辞書を受け取る
    kk_imgs = get_kk_imgs()
    # 初期状態（0, 0）の画像をセットする
    kk_img = kk_imgs[(0, 0)]
    kk_rct = kk_img.get_rect() 
    #kk_img = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    #kk_rct = kk_img.get_rect()
    kk_rct.center = 300, 200

    # 関数を呼び出して爆弾画像リストと加速度リストを受け取る 
    bb_imgs, bb_accs = init_bb_imgs()
    bb_img = bb_imgs[0]  # 初期状態として一番小さい爆弾(インデックス0)をセット
    #bb_img = pg.Surface((20, 20)) # 爆弾用の空のSurfaceを作る 
    #pg.draw.circle(bb_img, (255, 0, 0), (10, 10), 10) # 爆弾円を描く 
    #bb_img.set_colorkey((0, 0, 0))
    bb_rct = bb_img.get_rect() # 爆弾のRectを取得する
    bb_rct.centerx = random.randint(0, WIDTH) # 爆弾の初期横座標を設定する
    bb_rct.centery = random.randint(0, HEIGHT) # 爆弾の初期縦座標を設定する    
    vx, vy = +5, +5 # 爆弾の速度
    clock = pg.time.Clock()
    tmr = 0
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT: 
                return
            
        if kk_rct.colliderect(bb_rct): 
            gameover(screen)
            return
        screen.blit(bg_img, [0, 0]) 

        key_lst = pg.key.get_pressed()
        sum_mv = [0, 0]
        for key, mv in DELTA.items():
            if key_lst[key]: 
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        kk_rct.move_ip(sum_mv)
        kk_img = kk_imgs[tuple(sum_mv)]
        if check_bound(kk_rct) != (True, True):
            kk_rct.move_ip(-sum_mv[0], -sum_mv[1])
        
        screen.blit(kk_img, kk_rct)

        # 爆弾(bb_rct)からこうかとん(kk_rct)へのベクトルを計算して基本の速度(vx, vy)を更新する
        vx, vy = calc_orientation(bb_rct, kk_rct, (vx, vy))
        
        # tmr//500 で500フレームごとに段階を上げる。
        idx = min(tmr // 500, 9)
        
        # 加速度リストから値を取得し、現在の速度(vx, vy)に掛けて新しい速度を計算 
        avx = vx * bb_accs[idx]
        avy = vy * bb_accs[idx]
        
        # 爆弾の画像を段階に応じたサイズのものに切り替える 
        bb_img = bb_imgs[idx]
        
        # 画像サイズが変わったので、当たり判定用のRectのサイズも更新する 
        bb_rct.width = bb_img.get_rect().width
        bb_rct.height = bb_img.get_rect().height
        
        # 加速された速度(avx, avy)で爆弾を移動させる 
        bb_rct.move_ip(avx, avy)
        #screen.blit(kk_img, kk_rct)
        #bb_rct.move_ip(vx, vy)
        yoko, tate = check_bound(bb_rct)
        if not yoko:
            vx *= -1
        if not tate:
            vy *= -1

        screen.blit(bb_img, bb_rct)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
