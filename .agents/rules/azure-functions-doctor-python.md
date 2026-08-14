---
trigger: always_on
---

we will be developing a agentic application where user can query in natural language, like "hey!what should I eat now",based on the user feedback,depending upon the location he is currently and the time(basically it will be breakfast,lunch,evening snacks or dinner) it will search for the available online option and prioritize the cheapest and high rating food also that will be fastest to delivery.

-for food delivery apps like zomato,swiggy etc. we dont have the API but we will create synthetic data and run each of them seperately exposing the endpoint

-frontend should look like a modern chat applicaton,use ui-max skill for that. studio folder will contain frontend code.

-for mcp use mcp folder,for agents and orchestration use agent folder for api use the api folder inside platform\src.

frontend-use react with shadcn and lucid for icons
agents & orchestration use LangChain,LangGraph(use chatOpenAI)
DB-use postgresql with pgvector if necessary

keep the codebase clean and refactored

let the architect agent first plan everything,as clarifying question if required,DO THE CODING AFTER CONFIRMATION(DB SCRIPTS WE WILL RUN MANUALLY,SO PREPARE A FOLDER FOR ONLY DB SCRIPTS)