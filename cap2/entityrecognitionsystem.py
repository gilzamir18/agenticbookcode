from agenticblocks.blocks.llm.agent import LLMAgentBlock, AgentInput
from corpus import load_dataset, evaluate_model
import asyncio

class ModelEntityRecognitionSystem:
    def __init__(self, model):
        self.model = model

    async def extract_entities(self, text):
        input_data = AgentInput(prompt=text)
        output = await self.model.run(input_data)
        entities = [line.strip() for line in output.response.split("\n") if line.strip()]
        return entities

async def main():
    block = LLMAgentBlock(
        name="EntityRecognitionSystem",
        model="gemini/gemini-3.1-flash-lite-preview",
        description="Sistema de Reconhecimento de Entidades",
        system_prompt="""Você vai receber um texto e deve extrair as entidades mencionadas nele,
        listando-as uma por linha. Certifique-se de incluir apenas as entidades relevantes e evitar informações adicionais.""",
        max_iterations=0
    )
    dataset = load_dataset("corpus.txt", "entities.txt")
    results, averages = await evaluate_model(ModelEntityRecognitionSystem(block), dataset)
    for item in results:
        print(f"Text: {item['text']}")
        print(f"True Entities: {item['true_entities']}")
        print(f"Predicted Entities: {item['predicted_entities']}")
        print(f"Precision: {item['precision']:.2f}, Recall: {item['recall']:.2f}, F1 Score: {item['f1_score']:.2f}")
        print("-" * 50)
    print("=== Médias Gerais ===")
    print(f"Avg Precision: {averages['avg_precision']:.2f}")
    print(f"Avg Recall:    {averages['avg_recall']:.2f}")
    print(f"Avg F1 Score:  {averages['avg_f1_score']:.2f}")

if __name__ == "__main__":
    asyncio.run(main())