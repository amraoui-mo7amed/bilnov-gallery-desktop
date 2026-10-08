- [x] Remove the sidebar so:
    - the default and only widget is the library 
    - change the header Library 
    - Put the settings button as an icon-only in the header 
- [x] Rename the app to `olga+`
- [x] Create an icon for `olga+` and set it as app/fav/taskbar icon
- [x] In Settings widget rewmove the following:
    - the license details widget 
    - the client's phone and adress 
    - the details pane -that contains the numbers and depeloped by-
- [x] Work on the new translation strings 
- [x] Update how the app reads data inside storage folder so it follows this structure:
    ```
    - <category>
    -- <Subcategory>/<asset name>/<images>
    -- <Subcategory>/<asset name>/model/<arhcove file>
    ```
not 
```
    -<category>
    -- <asset name>/<images>
    -- <asset name>/model/<archive file>
```