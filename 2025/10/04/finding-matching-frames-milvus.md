# Finding matching frames across videos with Milvus

When I watched [*Необъяснимо, но факт: 3. Треугольник смерти (2005)*](../../../2025/10/04/nnf-003.md), I wanted to know the source for its archival footage. For example, when I searched for this frame with Google, it matched an image in https://www.dixi.tv/proekty1?id=140, a frame in *Дети великого августа (2001)*:

<img src="https://s3.amazonaws.com/writecomments.com/nnf/003/4/00_39_15.720 frame=58892.jpg" height=150>

Therefore, the frame occurs in both *Необъяснимо, но факт: 3. Треугольник смерти (2005)* and *Дети великого августа (2001)*. Because the 2005 film preceeds the 2001 film, it's only possible that the 2005 film borrowed the footage from the 2001 film (or they both borrow from an even earlier film). Emboldened by the power of reverse image search, I searched for another frame:

<img src="https://s3.amazonaws.com/writecomments.com/nnf/003/4/00_39_11.440 frame=58785.jpg" height=150>

...but none of the search engines I tried (Google, Yandex, TinEye, Bing, Lenso.ai, etc) returned any results. Perhaps, I already found the source film for this frame, and it is the aforementioned *Дети великого августа (2001)*. How would I confirm this without watching the whole film?

## How to tell if the same frame occurs in multiple videos?

With Milvus's reverse_image_search. Download its [docker-compose.yml](https://github.com/milvus-io/bootcamp/blob/1ab4de24510aaa5f28095a34059991a821f204e9/applications/image/reverse_image_search/docker-compose.yaml) into an empty directory and run this command in that directory:

```sh
docker compose up
```

Running the command will create two subdirectories: `data` and `volumes`, and your local network will begin hosting Milvus's web services: http://localhost:8001/, http://localhost:5000/docs, etc.

Suppose *Дети великого августа (2001)* is accessible from https://www.youtube.com/watch?v=Udb9yuZYzgo. Let's download it and save it as Udb9yuZYzgo.mp4:

```sh
yt-dlp -f "bestvideo[height<=360]" -o "%(id)s.%(ext)s" Udb9yuZYzgo
```

`bestvideo[height<=360]` is a [filtering format](https://github.com/yt-dlp/yt-dlp/tree/66cf3e1001b6d9a2829fe834c3f9103b0890918e?tab=readme-ov-file#filtering-formats), and `id` and `ext` are [output templates](https://github.com/yt-dlp/yt-dlp/tree/66cf3e1001b6d9a2829fe834c3f9103b0890918e?tab=readme-ov-file#output-template). We don't need the resolution to be higher than 360p for the image search. It's better if the images are smaller: they will take less memory, processing time, etc.

Now that we have `Udb9yuZYzgo.mp4`, let's also make `keyframes.sh`:

```sh
mkdir -p "$1"-keyframes
ffmpeg -i "$1" -vf "select='eq(pict_type,I)',showinfo" -vsync vfr -frame_pts true "$1"-keyframes/"$1"_%d.jpg
```

Now let's make a directory `Udb9yuZYzgo.mp4-keyframes` full of the keyframes and move it to the data directory:

```sh
sh keyframes.sh Udb9yuZYzgo.mp4
mv Udb9yuZYzgo.mp4-keyframes data
```

Now let's load these keyframes into Milvus (per http://localhost:5000/docs#/default/load_images_img_load_post):

```sh
curl 'http://127.0.0.1:5000/img/load' -H 'Content-Type: application/json;charset=UTF-8' --data-raw '{"File":"/data/Udb9yuZYzgo.mp4-keyframes", "Table":"nnf003"}'
```

You will be able to track the progress of the load operation in the window running `docker compose up` from above, with lines like this:

```
img-search-webserver  | 2025-10-05 03:46:11,934 ｜ INFO ｜ load.py ｜ extract_features ｜ 36 ｜ Extracting feature from image No. 43 , 1041 images in total
```

For example, when we see the above line, we know we're 43/1041 through the loading process. The curl command above will also respond with the success message once all the images are loaded:

```
"Successfully loaded data!"
```

Then, we can drag the frame above into http://localhost:8001/ and see if there's a match:

<img width="3108" height="1858" alt="image" src="https://github.com/user-attachments/assets/b1d4a23c-6c84-4ac3-ae8c-3effc35ab3c9" style="max-width: 100%;height: auto;max-height: 1858px;" />

It seems there is no match. But wait, we didn't specify the table. These are the images I've been loading with http://127.0.0.1:5000/img/load without specifying the table. The img-search-webclient doesn't let us specify the table conveniently, so we have to improvise. If we ask the browser to append `?table_name=nnf003` to every query to http://127.0.0.1:5000/img/search, that is use the table that contains the keyframes from the suspected origin film, we see that the frame of interest indeed matches a frame in the film whose keyframes just loaded into the Milvus table called nnf003:

<img width="3096" height="1858" alt="image" src="https://github.com/user-attachments/assets/38665a31-55b0-48f3-9c9d-9ea06192e20c" style="max-width: 100%;height: auto;max-height: 1858px;" />

One way to do so is through a browser extension called [Request Header/Query Param Override MV3](https://chromewebstore.google.com/detail/request-headerquery-param/cfgjehpalgepkcfekgjgmklehchiidgi). The query parameter `table_name` on the search endpoint is documented in http://localhost:5000/docs#/default/search_images_img_search_post. I actually loaded the keyframes without specifying the table above, but since there were already over 90k images in the root table, the performance was that much degraded, and so it didn't find the match, even though the matching image was loaded. So, keep your tables small if you want high accuracy. When Milvus isn't overwhelmed, its performance is magical.

<img width="3134" height="723" alt="image" src="https://github.com/user-attachments/assets/aa509c43-443e-4269-92ca-cdcf7137a449" style="max-width: 100%;height: auto;max-height: 723px;" />

If you copy the image address, you will know exactly which frame was the match, e.g.:

```
http://127.0.0.1:5000/data?image_path=/data/Udb9yuZYzgo.mp4-keyframes/Udb9yuZYzgo.mp4_14880.jpg
```

That is, the frame 58785 of *Необъяснимо, но факт: 3. Треугольник смерти (2005)* matches the frame 14880 of *Дети великого августа (2001)*. You could put all of the above in a shell script that accepts two videos as parameters, and it will output a table of matching frames with two columns: the frame number in video 1, the matching frame number in video 2. You could easily establish a mapping between the two videos, frame by frame.

# Next

* [Необъяснимо, но факт: 1. В объятиях смерти](../../../2025/09/27/nnf-001.md)
* [Необъяснимо, но факт: 2. Кыштымский пришелец](../../../2025/09/25/nnf-002.md)
* [Необъяснимо, но факт: 4. Озеро безумия](../../../2025/10/12/nnf-004.md)
