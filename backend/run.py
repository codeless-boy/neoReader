import sys
import os
# Add the pip packages path
sys.path.append("E:\\repo\\pip_packages")
# Add current directory to path so app.main is found
sys.path.append(os.getcwd())

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
