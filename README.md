# NASEM 2021 Dairy Model - Shiny App
This is the source code for a shiny app (using Shiny for Python) that imports the `nasem_dairy` package from https://github.com/CNM-University-of-Guelph/NASEM-Model-Python

# Deployment
This app is deployed to shinyapps.io by running:
```
rsconnect deploy shiny .
```

Currently deployed at: https://dave-innes-uog.shinyapps.io/nasem_shiny/

The `rsconnect` package requires configuring: https://shiny.posit.co/py/docs/deploy-cloud.html

In addition, the deployment will install the packages in `requirements.txt`. The `nasem_dairy` package in this file points to the github repo so that it can retrieve and install the package directly. 

# Local use
To run shiny app locally, download the files in this repo and install the `shiny` package + the VS Code extension: https://shiny.posit.co/py/docs/install.html. Then, when the `app.py` file is opened in VS Code it will show a 'Run Shiny App' button which will open it in a browser window. It assumes that the `diet_database.db` is in the same directory as the `app.py` file.

