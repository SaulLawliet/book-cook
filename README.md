# Book Cook

## 缘由

为了在 `Kindle` 阅读[《Re:从零开始的异世界生活》](https://www.wenku8.net/book/1861.htm),
而制作的 `ePub` 电子书生成器.

Q: 为什么不直接制作 `Kindle` 支持格式的电子书呢?  
A: 根据作者经验, 直接制作 `.mobi` 或 `.azw3` 的库比较少, 而且生成的电子书品质不佳.
然而用 `.epub` 转换成 `.azw3` 则可获得最佳体验(目录、注音等).
并且 `.epub` 也是使用最广泛的电子书格式.
转化工具推荐使用 `ebook-convert`.

## 描述

实现主要参考了 [youtube-dl](https://github.com/ytdl-org/youtube-dl),
目标是: 支持 **多个站点**!

## 使用

```sh
git clone git@github.com:SaulLawliet/book-cook.git
cd book-cook
pip install -r requirements.txt

python -m book_cook -h
```

## 支持的站点(按字母排序)

> 如果是有版权的书, 一定不要传播哦❤️

- [轻小说文库](https://www.wenku8.net/index.php): 2022-09-09
- [极客时间](https://time.geekbang.org/): 2022-11-10
- 本地txt文件: 2023-03-06

## 下载制作好的电子书

- [Google Drive](https://drive.google.com/drive/folders/1f2_lH86DJ1Go-iWv1852mrdD_Wsn4QX5?usp=sharing)
- 百度网盘: 链接: https://pan.baidu.com/s/1kZTGBidtbZd-JHlhiFJCZw 提取码: n4tv

## 其他

目前站点样本仅一个, 代码的实现主要保证目前能用, 所以 `基础函数库` 不是很完善. 😛

相信随着支持站点的增多, 我们的 `基础函数库` 会越来越强大! 🤩

如果需要 `新增站点` 或 `有任何的问题`, 请提交 `Issues`. 🥰

如果这个项目有帮到你, 你可以点个 `Star` 或 分享给你的小伙伴. 😘
