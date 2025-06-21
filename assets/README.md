# Build local PyScript for offline use

1. Clone repo

```bash
git clone https://github.com/pyscript/pyscript.git
```

2. Go to the downloaded repository

```bash
cd pyscript
```

3. Create venv

```bash
python3 -m venv my_pyscript_dev_venv
```

4. Activate venv

```bash
source my_pyscript_dev_venv/bin/activate
```

5. Run setup (requires Python and Node.js)

```bash
make setup
```

6. Format the code

```bash
make fmt
```

7. Check formatting

```bash
make fmt-check
```

8. Run pre-commit checks

```bash
make precommit-check
```

9. Build the PyScript

```bash
make build
```

10. Copy the `pyscript/core/dist/` (build created in the previous step) into your project

```bash
cp pyscript/core/dist/* YOUR_PROJECT_DIR/public/pyscript
```

11. Create a `./public/index.html` file that loads the local PyScript

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PyScript Offline</title>
  <script type="module" src="/pyscript/core.js"></script>
  <link rel="stylesheet" href="/pyscript/core.css">
</head>
<body>
  <script type="py">
    from pyscript import document

    document.body.append("Hello from PyScript")
  </script>
</body>
</html>
```

12. Run this project directly (after being sure that `index.html` file is saved into the `public/` folder)

```python
python -m http.server -d ./public/
```

13. (**OPTIONAL**) Local MicroPython interpreter

    - Install node module

    ```bash
    npm i @micropython/micropython-webassembly-pyscript
    ```

    - Create a folder in our public space

    ```bash
    mkdir -p ./public/micropython
    ```
    
    - Copy related files into such folder
    
    ```bash
    cp ./node_modules/@micropython/micropython-webassembly-pyscript/micropython.* ./public/micropython/
    ```
    
    - The folder should contain at least both `micropython.mjs` and `micropython.wasm` files.

    - Test the config with the example shown below

    ```html
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>PyScript Offline</title>
      <script type="module" src="/pyscript/core.js"></script>
      <link rel="stylesheet" href="/pyscript/core.css">
    </head>
    <body>
      <mpy-config>
        interpreter = "/micropython/micropython.mjs"
      </mpy-config>
      <script type="mpy">
        from pyscript import document
    
        document.body.append("Hello from PyScript")
      </script>
    </body>
    </html>
    ```
    
14. (**OPTIONAL**) Local Pyodide interpreter

    - Locally install the pyodide module
    
    ```bash
    npm i pyodide
    ```
    - Create a folder in our public space
    
    ```bash
    mkdir -p ./public/pyodide
    ```
    - Move all necessary files into that folder
    
    ```bash
    cp ./node_modules/pyodide/pyodide* ./public/pyodide/
    ```
    
    ```bash
    cp ./node_modules/pyodide/python_stdlib.zip ./public/pyodide/
    ```
    - Please note that the pyodide-lock.json file is needed, so please don't change that cp operation as all pyodide* files need to be moved.
    
    - Test the config with the example shown below
    
    ```html
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>PyScript Offline</title>
      <script type="module" src="/pyscript/core.js"></script>
      <link rel="stylesheet" href="/pyscript/core.css">
    </head>
    <body>
      <py-config>
        interpreter = "/pyodide/pyodide.mjs"
      </py-config>
      <script type="py">
        from pyscript import document
    
        document.body.append("Hello from PyScript")
      </script>
    </body>
    </html>
    ```
    
15. (**OPTIONAL**) Local Pyodide packages

    - Download the [package bundle](https://github.com/pyodide/pyodide/releases/tag/0.26.2) (>200 MB !!!; It contains each package that is required by Pyodide, and Pyodide will only load packages when needed.)

    - Copy the files and folders inside the `pyodide-0.26.2/pyodide/*` directory into our `./public/pyodide/*` folder
    
    ```bash
    cp pyodide-0.26.2/pyodide/* ./public/pyodide/*
    ```
    - Test the config with the example shown below
    
    ```html
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>PyScript Offline</title>
      <script type="module" src="/pyscript/core.js"></script>
      <link rel="stylesheet" href="/pyscript/core.css">
    </head>
    <body>
      <py-config>
        interpreter = "/pyodide/pyodide.mjs"
        packages = ["pandas"]
      </py-config>
      <script type="py">
        import pandas as pd
        x = pd.Series([1,2,3,4,5,6,7,8,9,10])
    
        from pyscript import document
        document.body.append(str([i**2 for i in x]))
      </script>
    </body>
    </html>
    ```
    
## Sources

1. [https://docs.pyscript.net/2025.5.1/user-guide/offline/#pyscipt-core-from-source](https://docs.pyscript.net/2025.5.1/user-guide/offline/#pyscipt-core-from-source)
2. [https://docs.pyscript.net/2025.5.1/developers/](https://docs.pyscript.net/2025.5.1/developers/)