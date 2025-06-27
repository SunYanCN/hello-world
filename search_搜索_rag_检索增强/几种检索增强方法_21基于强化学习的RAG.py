
# 检索增强生成 （RAG） 是一种将信息检索与生成模型相结合的混合方法。它通过整合外部知识来增强语言模型的性能，从而提高准确性和事实正确性。

####################################################################################################################################
# 方法21：
# 将使用强化学习(RL) RAG方法，使用提供的文档生成给定问题的答案。

## 目录

# - 环境设置
# - 数据预处理
# - 文档嵌入生成
# - 向量存储实现
# - 简单检索实现
# - 余弦相似度
# - 相似度搜索
# - LLM响应生成
# - 基本RAG管道
# - 基本RAG评估
# - RAG中的强化学习
# - 状态、动作空间和奖励方法
# - 策略网络
# - 单个RL步骤
# - 训练参数和策略更新
# - 训练循环
# - 性能比较逻辑
# - 评估框架
# - 评估RL与简单RAG
# - 保存比较结果
# - 结论

## 环境设置

# 导入os模块以与操作系统交互
import os
# 导入OpenAI模块以使用OpenAI的API
from openai import OpenAI
# 导入numpy进行数值运算
import numpy as np

# 导入json处理JSON数据
import json

# 导入typing模块进行类型提示
from typing import Dict, List, Tuple, Optional, Union

# 使用OpenAI客户端设置API连接
# 替换base_url和api_key为你自己的值

client = OpenAI(
    base_url="https://api.studio.nebius.com/v1/",
    api_key=os.environ["OPENAI_API_KEY"]
)

# 数据预处理
# 现在我们进入数据预处理阶段，需要加载数据并进行预处理。让我们创建一个函数，从目录中加载所有.txt文件，并返回一个文档列表。
# 加载目录中所有文档的函数
def load_documents(directory_path: str) -> List[str]:
    """加载指定目录中的所有文本文件。

    Args:
        directory_path (str): 包含文本文件的目录路径。

    Returns:
        List[str]: 包含每个文本文件内容的字符串列表。
    """
    documents = []  # 初始化一个空列表存储文档内容
    for filename in os.listdir(directory_path):  # 遍历目录中的所有文件
        if filename.endswith(".txt"):  # 检查文件是否为.txt扩展名
            # 以UTF-8编码打开文件并将其内容添加到列表中
            with open(os.path.join(directory_path, filename), 'r', encoding='utf-8') as file:
                documents.append(file.read())
    return documents  # 返回文档内容列表


# 我们需要创建一个函数，加载文档后对其进行分块处理。我们使用100个字符的块大小，但你可以根据需要调整。
# 将文档分割成块的函数
def split_into_chunks(documents: List[str], chunk_size: int = 30) -> List[str]:
    """将文档分割成指定大小的小块。

    Args:
        documents (List[str]): 要分割成块的文档字符串列表。
        chunk_size (int): 每个块中的最大单词数。默认为100。

    Returns:
        List[str]: 包含所有块的字符串列表，每个块最多包含chunk_size个单词。
    """
    chunks = []  # 初始化一个空列表存储块
    for doc in documents:  # 遍历每个文档
        words = doc.split()  # 将文档按单词分割
        # 创建指定大小的块
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])  # 将单词组合成块
            chunks.append(chunk)  # 将块添加到列表中
    return chunks  # 返回块列表


# 此步骤是可选的，其中我们通过删除特殊字符、转换为小写等方式对每个块进行预处理。
# 预处理文本的函数
def preprocess_text(text: str) -> str:
    """通过转换为小写和删除特殊字符来预处理输入文本。

    Args:
        text (str): 要预处理的输入文本。

    Returns:
        str: 仅包含字母数字字符和空格的预处理文本。
    """
    # 将文本转换为小写
    text = text.lower()
    # 删除特殊字符，仅保留字母数字字符和空格
    text = ''.join(char for char in text if char.isalnum() or char.isspace())
    return text


# 如果你使用了之前的预处理步骤，可以创建一个函数来预处理所有块。
# 预处理所有块的函数
def preprocess_chunks(chunks: List[str]) -> List[str]:
    """对所有文本块应用预处理。

    Args:
        chunks (List[str]): 要预处理的文本块列表。

    Returns:
        List[str]: 预处理后的文本块列表。
    """
    # 对列表中的每个块应用preprocess_text函数
    return [preprocess_text(chunk) for chunk in chunks]


# 现在我们已经实现了所有数据预处理函数，可以从目录中加载文档，将它们分割成块，并对块进行预处理。
# 指定包含文本文件的目录路径
directory_path = "data"

# 从指定目录加载所有文本文档
documents = load_documents(directory_path)

# 将加载的文档分割成较小的文本块
chunks = split_into_chunks(documents)

# 对块进行预处理（例如，转小写，删除特殊字符）
preprocessed_chunks = preprocess_chunks(chunks)

# 文档嵌入生成
# 在上一步中，我们对文档进行了分块处理。现在是时候为块数据集生成嵌入。由于RAG的知识库通常非常大，因此我们需要批量生成嵌入。让我们创建一个核心函数，用于批量生成块的嵌入。
# 为单个批次的文本块生成嵌入的函数
def generate_embeddings_batch(chunks_batch: List[str], model: str = "BAAI/bge-en-icl") -> List[List[float]]:
    """使用OpenAI客户端为一批文本块生成嵌入。

    Args:
        chunks_batch (List[str]): 要生成嵌入的一批文本块。
        model (str): 用于嵌入生成的模型。默认为"BAAI/bge-en-icl"。

    Returns:
        List[List[float]]: 包含所有块嵌入的列表，每个嵌入是一个浮点数列表。
    """
    # 使用OpenAI客户端为输入批次创建嵌入
    response = client.embeddings.create(
        model=model,  # 指定用于嵌入生成的模型
        input=chunks_batch  # 提供要处理的文本块列表作为输入
    )
    # 从响应中提取嵌入并返回
    embeddings = [item.embedding for item in response.data]
    return embeddings


# 接下来，我们定义一个函数，为所有文本块生成嵌入。该函数将文本块列表作为输入，并使用OpenAI客户端为每个块批次生成嵌入。函数返回一个包含所有块嵌入的NumPy数组。

# 为所有块生成嵌入的函数
def generate_embeddings(chunks: List[str], batch_size: int = 10) -> np.ndarray:
    """为所有文本块生成嵌入。

    Args:
        chunks (List[str]): 要生成嵌入的文本块列表。
        batch_size (int): 每批处理的块数。默认为10。

    Returns:
        np.ndarray: 包含所有块嵌入的NumPy数组。
    """
    all_embeddings = []  # 初始化一个空列表存储所有嵌入

    # 遍历块，按批次处理
    for i in range(0, len(chunks), batch_size):
        # 提取当前批次的块
        batch = chunks[i:i + batch_size]
        # 为当前批次生成嵌入
        embeddings = generate_embeddings_batch(batch)
        # 将当前批次的嵌入扩展到所有嵌入列表中
        all_embeddings.extend(embeddings)

    # 将嵌入列表转换为NumPy数组并返回
    return np.array(all_embeddings)


# 让我们创建另一个函数，将嵌入保存到JSON文件中。
# 保存嵌入到文件的函数
def save_embeddings(embeddings: np.ndarray, output_file: str) -> None:
    """将嵌入保存到JSON文件中。

    Args:
        embeddings (np.ndarray): 要保存的嵌入NumPy数组。
        output_file (str): 输出JSON文件的路径，嵌入将保存到此文件。

    Returns:
        None
    """
    # 以UTF-8编码打开指定文件
    with open(output_file, 'w', encoding='utf-8') as file:
        # 将NumPy数组转换为列表并保存为JSON
        json.dump(embeddings.tolist(), file)


# 现在我们已经实现了所有嵌入生成函数，可以为预处理后的文本块生成嵌入，并将它们保存到JSON文件中。
# 确保块已预处理后再生成嵌入
preprocessed_chunks = preprocess_chunks(chunks)

# 为预处理后的块生成嵌入
embeddings = generate_embeddings(preprocessed_chunks)

# 将生成的嵌入保存到名为"embeddings.json"的JSON文件中
save_embeddings(embeddings, "embeddings.json")

# 向量存储实现
# 由于我们没有使用任何Python库进行向量存储，我们将使用一个简单的字典实现向量存储。
# 初始化内存中的向量存储，作为字典
# 键是唯一的标识符（整数），值是包含嵌入和对应文本块的字典
vector_store: dict[int, dict[str, object]] = {}


# 将嵌入和对应的文本块添加到向量存储中的函数
def add_to_vector_store(embeddings: np.ndarray, chunks: List[str]) -> None:
    """将嵌入及其对应的文本块添加到向量存储中。

    Args:
        embeddings (np.ndarray): 要添加的嵌入NumPy数组。
        chunks (List[str]): 与嵌入对应的文本块列表。

    Returns:
        None
    """
    # 同时遍历嵌入和块
    for embedding, chunk in zip(embeddings, chunks):
        # 将每个嵌入及其对应的块添加到向量存储中
        # 使用向量存储的当前长度作为唯一的键
        vector_store[len(vector_store)] = {"embedding": embedding, "chunk": chunk}


# 简单检索实现
# 我们知道，要检索与给定查询最相似的文本块，可以使用查询嵌入与所有文本块嵌入之间的余弦相似度。余弦相似度越高，文本块越相似。然后，我们可以根据相似度分数对块进行排序，并返回最相似的前k个块。
#
# 让我们实现一个基于余弦相似度的简单检索函数。

# 计算两个向量之间余弦相似度的函数
def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """计算两个向量之间的余弦相似度。

    Args:
        vec1 (np.ndarray): 第一个向量。
        vec2 (np.ndarray): 第二个向量。

    Returns:
        float: 两个向量之间的余弦相似度，范围在-1到1之间。
    """
    # 计算两个向量的点积
    dot_product = np.dot(vec1, vec2)
    # 计算第一个向量的模（范数）
    norm_vec1 = np.linalg.norm(vec1)
    # 计算第二个向量的模（范数）
    norm_vec2 = np.linalg.norm(vec2)
    # 返回余弦相似度，即点积与模的乘积的比值
    return dot_product / (norm_vec1 * norm_vec2)


# 当我们计算查询与所有块之间的余弦相似度时，可以执行相似度搜索。根据top_k参数，检索最相似的前k个块。
# 在向量存储中执行相似度搜索的函数
def similarity_search(query_embedding: np.ndarray, top_k: int = 5) -> List[str]:
    """在向量存储中执行相似度搜索，并返回最相似的前k个块。

    Args:
        query_embedding (np.ndarray): 查询的嵌入向量。
        top_k (int): 要检索的最相似块的数量。默认为5。

    Returns:
        List[str]: 包含最相似文本块的列表。
    """
    similarities = []  # 初始化一个列表存储相似度分数和对应的键

    # 遍历向量存储中的所有项目
    for key, value in vector_store.items():
        # 计算查询嵌入与存储嵌入之间的余弦相似度
        similarity = cosine_similarity(query_embedding, value["embedding"])
        # 将键和相似度分数作为元组附加到列表中
        similarities.append((key, similarity))

    # 根据相似度分数按降序排序列表
    similarities = sorted(similarities, key=lambda x: x[1], reverse=True)

    # 根据键检索最相似的块
    return [vector_store[key]["chunk"] for key, _ in similarities[:top_k]]


# 一旦我们准备好相似度搜索函数，就可以在上面构建一个检索函数，根据查询提供相关的块。
# 为查询检索相关文档块的函数
def retrieve_relevant_chunks(query_text: str, top_k: int = 5) -> List[str]:
    """为给定查询文本检索最相关的文档块。

    Args:
        query_text (str): 要检索相关块的查询文本。
        top_k (int): 要检索的最相关块的数量。默认为5。

    Returns:
        List[str]: 包含最相关文本块的列表。
    """
    # 使用嵌入模型为查询文本生成嵌入
    query_embedding = generate_embeddings([query_text])[0]

    # 执行相似度搜索以找到最相关的块
    relevant_chunks = similarity_search(query_embedding, top_k=top_k)

    # 返回相关块列表
    return relevant_chunks


# 现在我们已经实现了所有检索函数，可以测试检索系统在示例查询上的性能。

# 将生成的嵌入及其对应的预处理块添加到向量存储中
add_to_vector_store(embeddings, preprocessed_chunks)

# 定义一个查询文本，以检索相关的文档块
query_text = "什么是量子计算？"

# 根据查询文本从向量存储中检索最相关的块
relevant_chunks = retrieve_relevant_chunks(query_text)

# 打印每个检索到的相关块的前50个字符
for idx, chunk in enumerate(relevant_chunks):
    print(f"块 {idx + 1}: {chunk[:50]} ... ")
    print("-" * 50)  # 打印分隔线

# LLM响应生成
# 当我们有一个查询和一组相关的文档块时，可以使用大型语言模型（LLM）根据查询和检索到的信息生成响应。在本节中，我们将使用OpenAI API根据查询和检索到的上下文生成查询的响应。

# 首先，我们需要一个函数，根据查询和相关块构建LLM的输入提示。

# 构建包含上下文的提示的函数
def construct_prompt(query: str, context_chunks: List[str]) -> str:
    """通过结合查询和检索到的上下文块构建提示。

    Args:
        query (str): 要构建提示的查询文本。
        context_chunks (List[str]): 包含相关上下文块的列表。

    Returns:
        str: 要用于LLM输入的构建提示。
    """
    # 将所有上下文块组合成一个字符串，块之间用换行符分隔
    context = "\n".join(context_chunks)

    # 定义指导LLM行为的系统消息
    system_message = (
        "你是一个乐于助人的助手。仅使用提供的上下文来回答问题。"
        "如果上下文中不包含所需信息，请说'我没有足够的信息来回答这个问题。'"
    )

    # 通过结合系统消息、上下文和查询构建最终提示
    prompt = f"系统: {system_message}\n\n上下文:\n{context}\n\n问题:\n{query}\n\n回答:"
    return prompt


# 为了生成LLM响应，我们需要实现一个函数，将构建的输入提示发送到OpenAI API以生成响应。

# 使用OpenAI聊天模型生成响应的函数
def generate_response(
        prompt: str,
        model: str = "google/gemma-2-2b-it",
        max_tokens: int = 512,
        temperature: float = 1,
        top_p: float = 0.9,
        top_k: int = 50
) -> str:
    """使用OpenAI聊天模型根据构建的提示生成响应。

    Args:
        prompt (str): 要提供给聊天模型的输入提示。
        model (str): 用于生成响应的模型。默认为"google/gemma-2-2b-it"。
        max_tokens (int): 响应中的最大令牌数。默认为512。
        temperature (float): 采样温度，控制响应的多样性。默认为0.5。
        top_p (float): 核采样中的概率质量。默认为0.9。
        top_k (int): 考虑的最高概率令牌数。默认为50。

    Returns:
        str: 聊天模型生成的响应。
    """
    # 使用OpenAI客户端创建聊天完成
    response = client.chat.completions.create(
        model=model,  # 指定用于生成响应的模型
        max_tokens=max_tokens,  # 响应中的最大令牌数
        temperature=temperature,  # 采样温度，控制响应的多样性
        top_p=top_p,  # 核采样中的概率质量
        extra_body={  # 请求的额外参数
            "top_k": top_k  # 考虑的最高概率令牌数
        },
        messages=[  # 提供上下文的消息列表
            {
                "role": "user",  # 消息发送者的角色（用户）
                "content": [  # 消息内容
                    {
                        "type": "text",  # 内容类型（文本）
                        "text": prompt  # 实际提示文本
                    }
                ]
            }
        ]
    )
    # 返回第一个选择的响应内容
    return response.choices[0].message.content


# 基本RAG管道
# 我们不能反复运行小段代码。因此，我们需要创建一个简单的RAG管道，它只需要一个参数（查询），并返回LLM响应。

# 实现基本的检索增强生成（RAG）管道的函数
def basic_rag_pipeline(query: str) -> str:
    """实现基本的检索增强生成（RAG）管道：检索相关块，构建提示，生成响应。

    Args:
        query (str): 要生成响应的输入查询。

    Returns:
        str: LLM根据查询和检索到的上下文生成的响应。
    """
    # 步骤1：检索与查询最相关的块
    relevant_chunks: List[str] = retrieve_relevant_chunks(query)

    # 步骤2：使用查询和检索到的块构建提示
    prompt: str = construct_prompt(query, relevant_chunks)

    # 步骤3：使用构建的提示生成LLM响应
    response: str = generate_response(prompt)

    # 返回生成的响应
    return response


# 评估基本RAG
# 现在我们已经实现了基本的RAG管道，可以使用它进行评估。我们的评估查询包含不同的目标段，如事实性查询和复杂性质。我们将测试RAG管道的事实知识。

# 让我们加载我们的评估查询及其预期答案。
# 打开验证数据文件并加载其内容作为字典
with open('data/val_rl.json', 'r') as file:
    validation_data = json.load(file)

# 使用基本RAG管道测试示例查询
sample_query = validation_data['basic_factual_questions'][0]['question']  # 提取查询文本
expected_answer = validation_data['basic_factual_questions'][0]['answer']  # 提取正确答案

# 打印示例查询和预期答案
print(f"示例查询: {sample_query}\n")
print(f"预期答案: {expected_answer}\n")

# 让我们测试基本RAG管道在评估查询上的性能。
# 打印消息，指示RAG管道正在运行
print("🔍 正在运行检索增强生成（RAG）管道...")
print(f"📥 查询: {sample_query}\n")

# 运行RAG管道并获取响应
response = basic_rag_pipeline(sample_query)

# 以更好的格式打印响应
print("🤖 AI响应:")
print("-" * 50)
print(response.strip())
print("-" * 50)

# 打印真实答案以进行比较
print("✅ 真实答案:")
print("-" * 50)
print(expected_answer)
print("-" * 50)

# 基本RAG管道似乎在当前状态下表现不佳。生成的响应不仅与真实答案无关，还缺少关键信息。

# 但在接下来的步骤中，我们将实现一个基于强化学习的RAG管道，以解决这些不足。这将帮助我们改进检索和生成过程，使响应更准确、上下文更相关。

# 敬请期待，我们将RAG管道提升到一个新的高度！🚀

# 强化学习在RAG中的应用
# 强化学习（Reinforcement Learning, RL）是一种机器学习类型，其中代理通过在环境中采取行动来学习如何做出决策，以最大化累积奖励的概念。与监督学习不同，代理没有明确被告知采取哪些行动，而是必须通过试错发现哪些行动会带来最大的奖励。
#
# 以下是强化学习系统的主要组成部分：
#
# 代理（Agent）：学习和决策的主体。
# 环境（Environment）：代理与其交互的世界。
# 状态（State）：代理在环境中当前的情况。
# 动作（Action）：代理可以采取的一系列可能行动。
# 奖励（Reward）：代理在采取行动后从环境中获得的反馈。
# 策略（Policy）：代理遵循的策略，以决定下一步行动。
# 强化学习的目标是学习一个策略π，使得在环境中累积奖励的期望最大化：


# 在RAG系统中，强化学习可以用于：
#
# 通过学习哪些文档最有帮助来改进检索
# 根据用户反馈调整提示构造
# 通过从成功响应中学习来优化生成过程
# 状态、动作空间和奖励方法
# 在编码RL算法时，首先要定义三件事：
#
# 状态（State）：当前环境的情况。在我们的情况下，初始状态是我们的基本RAG管道（查询、上下文、响应）。
# 动作空间（Action Space）：代理根据状态采取的决策。在我们的情况下，动作可以包括更改模型、修改上下文、更改查询等。
# 奖励（Reward）：代理在采取行动后获得的反馈。在我们的情况下，奖励可以是生成的响应与真实答案之间的相似度。我们的状态将随着训练不断变化。为此，我们需要在每次训练回合后保存状态，以便RL代理可以从中学习，并避免重复犯错。

# 定义强化学习代理的状态表示的函数
def define_state(
        query: str,
        context_chunks: List[str],
        rewritten_query: str = None,
        previous_responses: List[str] = None,
        previous_rewards: List[float] = None
) -> dict:
    """定义强化学习代理的状态表示。

    Args:
        query (str): 原始用户查询。
        context_chunks (List[str]): 从知识库检索到的上下文块。
        rewritten_query (str, optional): 查询的重新表述版本。
        previous_responses (List[str], optional): 之前生成的响应列表。
        previous_rewards (List[float], optional): 之前获得的奖励列表。

    Returns:
        dict: 包含所有相关信息的当前状态字典。
    """
    state = {
        "original_query": query,  # 用户的初始查询
        "current_query": rewritten_query if rewritten_query else query,  # 当前查询版本（可能已重新表述）
        "context": context_chunks,  # 从知识库检索到的上下文块
        "previous_responses": previous_responses if previous_responses else [],  # 之前生成的响应历史
        "previous_rewards": previous_rewards if previous_rewards else []  # 之前获得的奖励历史
    }
    return state


# 我们已经定义了RL代理的状态表示，包括用户查询、检索到的上下文块、重新表述的查询（如果有的话）、以及之前生成的响应和奖励历史。这个状态将指导代理生成更好的响应。
# 接下来，我们需要定义强化学习代理的动作空间。动作空间由代理在每一步可以采取的一系列可能动作组成。在本例中，我们定义了四个动作：

# rewrite_query：重新表述原始查询以改进检索
# expand_context：检索额外的上下文块
# filter_context：移除不相关的上下文块
# generate_response：根据当前查询和上下文生成响应

# 定义强化学习代理的动作空间的函数
def define_action_space() -> List[str]:
    """定义强化学习代理可以采取的动作集合。

    动作包括：
    - rewrite_query：重新表述原始查询以改进检索
    - expand_context：检索额外的上下文块
    - filter_context：移除不相关的上下文块
    - generate_response：根据当前查询和上下文生成响应

    Returns:
        List[str]: 可用动作的列表。
    """
    # 定义代理可以采取的动作集合
    actions = ["rewrite_query", "expand_context", "filter_context", "generate_response"]
    return actions


# 显然，当我们的RL代理采取行动时，它是基于当前状态和动作空间的。它将根据RAG管道生成的响应质量获得奖励。奖励函数基于生成的响应与真实答案之间的余弦相似度。

# 根据响应质量计算奖励的函数
def calculate_reward(response: str, ground_truth: str) -> float:
    """通过比较生成的响应与真实答案来计算奖励值。

    使用响应和真实答案嵌入之间的余弦相似度来确定响应与预期答案的接近程度。

    Args:
        response (str): RAG管道生成的响应。
        ground_truth (str): 预期的正确答案。

    Returns:
        float: 奖励值，范围在-1到1之间，值越高表示响应越接近真实答案。
    """
    # 为响应和真实答案生成嵌入
    response_embedding = generate_embeddings([response])[0]
    ground_truth_embedding = generate_embeddings([ground_truth])[0]

    # 计算嵌入之间的余弦相似度作为奖励
    similarity = cosine_similarity(response_embedding, ground_truth_embedding)
    return similarity


# 我们的目标是通过生成与真实答案相似的响应来最大化奖励。奖励值越高，表示生成的响应越接近预期答案。

# 策略网络
# 在之前，我们定义了状态、动作空间和奖励逻辑。接下来，我们需要创建一个策略网络，它将根据当前状态选择一个动作。

# 策略网络是一个函数，它接受当前状态和动作空间作为输入，并根据状态返回一个动作。

# 策略网络可以使用简单的启发式方法来选择动作。例如，如果没有之前的响应，策略网络可以优先重新表述查询。如果上下文块过多，策略网络可以选择过滤上下文。

# 定义策略网络以根据当前状态选择动作的函数
def policy_network(
        state: dict,
        action_space: List[str],
        epsilon: float = 0.2
) -> str:
    """定义一个策略网络，使用epsilon-greedy策略根据当前状态选择动作。

    Args:
        state (dict): 包含查询、上下文、响应和奖励的当前环境状态。
        action_space (List[str]): 代理可以采取的动作列表。
        epsilon (float): 探索概率，用于平衡探索与利用。默认为0.2。

    Returns:
        str: 从动作空间中选择的动作。
    """
    # 使用epsilon-greedy策略：随机探索与利用
    if np.random.random() < epsilon:
        # 探索：从动作空间中随机选择一个动作
        action = np.random.choice(action_space)
    else:
        # 利用：根据当前状态使用简单启发式选择最佳动作
        # 所以我们的策略网络的工作原理如下：
        # 如果没有之前的响应，优先重新表述查询。
        # 如果有之前的响应但奖励较低，尝试扩展上下文。
        # 如果上下文块过多，尝试过滤上下文。
        # 否则，生成响应。
        if len(state["previous_responses"]) == 0:
            action = "rewrite_query"
        elif state["previous_rewards"] and max(state["previous_rewards"]) < 0.7:
            action = "expand_context"
        elif len(state["context"]) > 5:
            action = "filter_context"
        else:
            action = "generate_response"

    return action

# 单个RL步骤
# 我们已经编码了RL管道的重要组成部分。对于任何进行过训练的开发人员来说，训练循环中的每一次迭代都是一个单个步骤，其中RL代理采取行动，计算奖励，更新状态等。因此，我们需要编码一个单个步骤的训练循环。让我们这样做。

# 执行单个RL步骤的函数
def rl_step(
        state: dict,
        action_space: List[str],
        ground_truth: str
) -> tuple[dict, str, float, str]:
    """执行单个RL步骤：选择一个动作，执行它，并计算奖励。

    Args:
        state (dict): 包含查询、上下文、响应和奖励的当前环境状态。
        action_space (List[str]): 代理可以采取的动作列表。
        ground_truth (str): 预期的正确答案，用于计算奖励。

    Returns:
        tuple: 包含以下内容的元组：
        - state (dict): 执行动作后更新的状态。
        - action (str): 策略网络选择的动作。
        - reward (float): 采取行动后获得的奖励。
        - response (str): 生成的响应（如果适用）。
    """
    # 使用策略网络选择一个动作
    action: str = policy_network(state, action_space)
    response: str = None  # 初始化响应为None
    reward: float = 0  # 初始化奖励为0

    # 执行选择的动作
    if action == "rewrite_query":
        # 重新表述查询以改进检索
        rewritten_query: str = rewrite_query(state["original_query"], state["context"])
        state["current_query"] = rewritten_query  # 更新状态中的当前查询
        # 根据重新表述的查询检索新的上下文
        new_context: List[str] = retrieve_relevant_chunks(rewritten_query)
        state["context"] = new_context  # 更新状态中的上下文

    elif action == "expand_context":
        # 扩展上下文，检索额外的块
        expanded_context: List[str] = expand_context(state["current_query"], state["context"])
        state["context"] = expanded_context  # 更新状态中的上下文

    elif action == "filter_context":
        # 过滤上下文，保留最相关的块
        filtered_context: List[str] = filter_context(state["current_query"], state["context"])
        state["context"] = filtered_context  # 更新状态中的上下文

    elif action == "generate_response":
        # 使用当前查询和上下文构建提示
        prompt: str = construct_prompt(state["current_query"], state["context"])
        # 生成LLM响应
        response: str = generate_response(prompt)
        # 根据响应与真实答案的相似度计算奖励
        reward: float = calculate_reward(response, ground_truth)
        # 更新状态中的响应和奖励历史
        state["previous_responses"].append(response)
        state["previous_rewards"].append(reward)

    # 返回更新后的状态、选择的动作、奖励和响应
    return state, action, reward, response


# 在我们的单个步骤函数中，首先使用策略网络选择一个动作。策略网络使用epsilon - greedy策略来平衡探索与利用。如果随机数小于epsilon，我们从动作空间中随机选择一个动作进行探索。否则，我们根据当前状态使用简单启发式选择最佳动作。

# 训练参数和策略更新
# 我们需要定义一些训练参数，用于训练循环，同时定义一个函数，根据获得的奖励更新策略。

# 虽然训练参数函数是可选的，但它可以用于RL管道的高级实现。

# 初始化训练参数的函数
def initialize_training_params() -> Dict[str, Union[float, int]]:
    """初始化训练参数，如学习率、回合数和折扣因子。

    Returns:
        Dict[str, Union[float, int]]: 包含初始化训练参数的字典。
    """
    params = {
        "learning_rate": 0.01,  # 策略更新的学习率
        "num_episodes": 100,  # 训练回合总数
        "discount_factor": 0.99  # 未来奖励的折扣因子
    }
    return params


# 与状态在RL过程中的变化类似，策略也需要根据获得的奖励进行更新。update_policy函数接受当前策略、状态、动作、奖励和学习率作为输入，并返回更新后的策略。

# 根据奖励更新策略的函数
def update_policy(
        policy: Dict[str, Dict[str, Union[float, str]]],
        state: Dict[str, object],
        action: str,
        reward: float,
        learning_rate: float
) -> Dict[str, Dict[str, Union[float, str]]]:
    """根据获得的奖励更新策略。

    Args:
        policy (Dict[str, Dict[str, Union[float, str]]]): 要更新的当前策略。
        state (Dict[str, object]): 当前环境状态。
        action (str): 代理采取的动作。
        reward (float): 采取行动后获得的奖励。
        learning_rate (float): 策略更新的学习率。

    Returns:
        Dict[str, Dict[str, Union[float, str]]]: 更新后的策略。
    """
    # 示例：简单的策略更新（将被更高级的RL算法替换）
    policy[state["query"]] = {
        "action": action,  # 存储采取的动作
        "reward": reward  # 存储获得的奖励
    }
    return policy


# 在上述update_policy逻辑中，我们在策略字典中存储了查询、采取的动作和获得的奖励。在更高级的RL算法中，策略更新将涉及更复杂的方法，如策略梯度或Q学习。

# 训练循环
# 现在我们已经编码了训练循环的每一个部分，可以将它们组合到一个函数中，实现RL增强的RAG系统的训练循环。

# 实现训练循环的函数
# 详细来说，training_loop函数执行以下操作：
#
# 初始化训练参数（如果未提供）。
# 获取简单RAG管道的初始性能以进行比较。
# 开始训练循环，执行指定数量的回合。
# 在每个回合中执行单个RL步骤。
# 更新奖励和动作历史。
# 每5个回合打印进度。
# 比较RL增强的RAG与简单RAG的奖励。
# 返回更新后的策略、奖励历史、动作历史，以及最佳响应。
# 性能比较逻辑
def training_loop(
        query_text: str,
        ground_truth: str,
        params: Optional[Dict[str, Union[float, int]]] = None
) -> Tuple[Dict[str, Dict[str, Union[float, str]]], List[float], List[List[str]], Optional[str]]:
    """实现RL增强的RAG训练循环。

    Args:
        query_text (str): 输入查询文本。
        ground_truth (str): 查询的预期正确答案。
        params (Optional[Dict[str, Union[float, int]]]): 训练参数，如学习率、回合数和折扣因子。如果为None，则使用默认参数。

    Returns:
        Tuple: 包含以下内容的元组：
        - policy (Dict[str, Dict[str, Union[float, str]]]): 训练后的策略。
        - rewards_history (List[float]): 每个回合获得的奖励列表。
        - actions_history (List[List[str]]): 每个回合采取的动作列表。
        - best_response (Optional[str]): 训练过程中生成的最佳响应。
    """
    # 如果未提供训练参数，则初始化默认参数
    if params is None:
        params = initialize_training_params()

    # 初始化变量以跟踪进度
    rewards_history: List[float] = []  # 存储每个回合奖励的列表
    actions_history: List[List[str]] = []  # 存储每个回合采取的动作的列表
    policy: Dict[str, Dict[str, Union[float, str]]] = {}  # 策略字典，存储动作和奖励
    action_space: List[str] = define_action_space()  # 定义动作空间
    best_response: Optional[str] = None  # 存储最佳响应的变量
    best_reward: float = -1  # 初始化最佳奖励为一个很低的值

    # 获取简单RAG管道的初始性能以进行比较
    simple_response: str = basic_rag_pipeline(query_text)
    simple_reward: float = calculate_reward(simple_response, ground_truth)
    print(f"简单RAG奖励: {simple_reward:.4f}")

    # 开始训练循环
    for episode in range(params["num_episodes"]):
        # 使用相同的查询重置环境
        context_chunks: List[str] = retrieve_relevant_chunks(query_text)
        state: Dict[str, object] = define_state(query_text, context_chunks)
        episode_reward: float = 0  # 初始化当前回合的奖励
        episode_actions: List[str] = []  # 初始化当前回合采取的动作列表

        # 每个回合的最大步骤数，以防止无限循环
        for step in range(10):
            # 执行单个RL步骤
            state, action, reward, response = rl_step(state, action_space, ground_truth)
            episode_actions.append(action)  # 记录采取的动作

            # 如果生成了响应，结束回合
            if response:
                episode_reward = reward  # 更新回合奖励

                # 跟踪最佳响应和奖励
                if reward > best_reward:
                    best_reward = reward
                    best_response = response

                break  # 退出循环，因为回合结束

        # 更新奖励和动作历史
        rewards_history.append(episode_reward)
        actions_history.append(episode_actions)

        # 每5个回合打印进度
        if episode % 5 == 0:
            print(f"回合 {episode}: 奖励 = {episode_reward:.4f}, 动作 = {episode_actions}")

    # 比较RL增强的RAG与简单RAG的奖励
    improvement: float = best_reward - simple_reward
    print(f"\n训练完成:")
    print(f"简单RAG奖励: {simple_reward:.4f}")
    print(f"最佳RL增强RAG奖励: {best_reward:.4f}")
    print(f"改进: {improvement:.4f} ({improvement * 100:.2f}%)")

    return policy, rewards_history, actions_history, best_response


# 此函数将输入查询文本、预期真实答案以及可选的训练参数作为输入。它返回更新后的策略、每个回合获得的奖励列表、每个回合采取的动作列表，以及训练过程中生成的最佳响应。

# 虽然我们可以手动比较简单RAG管道与RL增强的RAG管道，但一个函数肯定能帮助我们完成此任务。因此，让我们定义一个函数，比较简单RAG与RL增强的RAG的性能。

# 比较简单RAG与RL增强RAG的函数
def compare_rag_approaches(query_text: str, ground_truth: str) -> Tuple[str, str, float, float]:
    """比较简单RAG与RL增强RAG的输出。

    Args:
        query_text (str): 输入查询文本。
        ground_truth (str): 查询的预期正确答案。

    Returns:
        Tuple[str, str, float, float]: 包含以下内容的元组：
        - simple_response (str): 简单RAG管道生成的响应。
        - best_rl_response (str): RL增强RAG管道生成的最佳响应。
        - simple_similarity (float): 简单RAG响应与真实答案的相似度。
        - rl_similarity (float): RL增强RAG响应与真实答案的相似度。
    """
    print("=" * 80)
    print(f"查询: {query_text}")
    print("=" * 80)

    # 步骤1：使用简单RAG管道生成响应
    simple_response: str = basic_rag_pipeline(query_text)
    # 计算简单RAG响应与真实答案的相似度
    simple_similarity: float = calculate_reward(simple_response, ground_truth)

    print("\n简单RAG输出:")
    print("-" * 40)
    print(simple_response)
    print(f"与真实答案的相似度: {simple_similarity:.4f}")

    # 步骤2：训练RL增强的RAG模型
    print("\n训练RL增强的RAG模型...")
    # 初始化训练参数（如学习率、回合数、折扣因子）
    params: Dict[str, float | int] = initialize_training_params()
    # 将回合数设置为较小的值以进行演示
    params["num_episodes"] = 5

    # 运行训练循环以训练RL增强的RAG模型
    _, rewards_history, actions_history, best_rl_response = training_loop(
        query_text, ground_truth, params
    )

    # 如果训练过程中没有生成响应，使用当前查询和上下文生成一个响应
    if best_rl_response is None:
        # 检索与查询相关的块
        context_chunks: List[str] = retrieve_relevant_chunks(query_text)
        # 使用查询和检索到的上下文构建提示
        prompt: str = construct_prompt(query_text, context_chunks)
        # 生成LLM响应
        best_rl_response: str = generate_response(prompt)

    # 计算RL增强RAG响应与真实答案的相似度
    rl_similarity: float = calculate_reward(best_rl_response, ground_truth)

    print("\nRL增强RAG输出:")
    print("-" * 40)
    print(best_rl_response)
    print(f"与真实答案的相似度: {rl_similarity:.4f}")

    # 步骤3：评估和比较结果
    # 计算RL增强RAG模型相对于简单RAG模型的改进
    improvement: float = rl_similarity - simple_similarity

    print("\n评估结果:")
    print("-" * 40)
    print(f"简单RAG与真实答案的相似度: {simple_similarity:.4f}")
    print(f"RL增强RAG与真实答案的相似度: {rl_similarity:.4f}")
    print(f"改进: {improvement * 100:.2f}%")

    # 步骤4：绘制奖励历史（如果有足够的回合数且matplotlib可用）
    if len(rewards_history) > 1:
        try:
            import matplotlib.pyplot as plt
            # 绘制RL训练期间的奖励历史图
            plt.figure(figsize=(10, 6))
            plt.plot(rewards_history)
            plt.title('RL训练期间的奖励历史')
            plt.xlabel('回合')
            plt.ylabel('奖励')
            plt.grid(True)
            plt.show()
        except ImportError:
            # 如果没有matplotlib，打印消息而不是绘图
            print("matplotlib不可用，无法绘制奖励图")

    # 返回结果：两种方法的响应及其相似度
    return simple_response, best_rl_response, simple_similarity, rl_similarity


# 所以我们的性能比较逻辑并不复杂，而是基于以下4个步骤：
#
# 使用简单RAG管道生成响应。
# 使用训练循环训练RL增强的RAG模型。
# 评估并比较结果。
# 绘制奖励历史（如果可用）。
# 评估框架（可选）
# 此步骤是可选的，但如果你想在验证数据上评估所有评估查询，可以使用以下代码。
#
# 首先，为了评估检索到的块与真实答案的相关性，我们需要一个函数来评估检索到的块的相关性。

# 评估检索到的块的相关性的函数
def evaluate_relevance(retrieved_chunks: List[str], ground_truth_chunks: List[str]) -> float:
    """通过比较检索到的块与真实块来评估相关性。

    Args:
        retrieved_chunks (List[str]): 检索系统返回的文本块列表。
        ground_truth_chunks (List[str]): 真实文本块列表，用于比较。

    Returns:
        float: 检索到的块与真实块之间的平均相关性分数。
    """
    relevance_scores: List[float] = []  # 初始化一个列表存储相关性分数

    # 遍历检索块与真实块的配对
    for retrieved, ground_truth in zip(retrieved_chunks, ground_truth_chunks):
        # 计算检索块与真实块嵌入之间的余弦相似度
        relevance: float = cosine_similarity(
            generate_embeddings([retrieved])[0],
            generate_embeddings([ground_truth])[0]
        )
        # 将相关性分数添加到列表中
        relevance_scores.append(relevance)

    # 返回相关性分数的平均值
    return np.mean(relevance_scores)


# 为了评估生成响应的准确性，我们可以使用响应与真实答案之间的余弦相似度。因此，我们定义一个函数，根据这种相似度指标评估响应的准确性。

# 评估生成响应准确性的函数
def evaluate_accuracy(responses: List[str], ground_truth_responses: List[str]) -> float:
    """通过比较生成的响应与真实响应来评估准确性。

    Args:
        responses (List[str]): 要评估的生成响应列表。
        ground_truth_responses (List[str]): 用于比较的真实响应列表。

    Returns:
        float: 响应准确性的平均分数，计算为响应嵌入与真实响应嵌入之间的余弦相似度的平均值。
    """
    accuracy_scores: List[float] = []  # 初始化一个列表存储准确性分数

    # 遍历每个生成响应与真实响应的配对
    for response, ground_truth in zip(responses, ground_truth_responses):
        # 计算响应与真实响应嵌入之间的余弦相似度
        accuracy: float = cosine_similarity(
            generate_embeddings([response])[0],
            generate_embeddings([ground_truth])[0]
        )
        # 将准确性分数添加到列表中
        accuracy_scores.append(accuracy)

    # 返回准确性分数的平均值
    return np.mean(accuracy_scores)


# 我们还需要衡量响应质量，并为此分配一个相关分数，用于强化学习过程。

# 评估响应质量的函数
def evaluate_response_quality(responses: List[str]) -> float:
    """使用启发式方法或外部模型评估响应质量。

    Args:
        responses (List[str]): 要评估的生成响应列表。

    Returns:
        float: 响应质量的平均分数，范围在0到1之间。
    """
    quality_scores: List[float] = []  # 初始化一个列表存储每个响应的质量分数

    for response in responses:
        # 示例启发式：根据响应长度计算质量分数
        # 将长度标准化为最多100个单词，并将分数限制在1.0以下
        quality: float = len(response.split()) / 100
        quality_scores.append(min(quality, 1.0))  # 将受限的质量分数添加到列表中

    # 返回所有响应质量分数的平均值
    return np.mean(quality_scores)


# 然后，我们可以在验证数据集上评估RL增强的RAG模型的性能：
# 评估RAG性能的函数

def evaluate_rag_performance(
    queries: List[str],
    ground_truth_chunks: List[str],
    ground_truth_responses: List[str]
    ) -> Dict[str, float]:
    """使用相关性、准确性和响应质量指标评估RAG管道的性能。


    参数:
        queries (List[str]): 要评估的查询字符串列表。
        ground_truth_chunks (List[str]): 与查询对应的真实文本块列表。
        ground_truth_responses (List[str]): 与查询对应的真实响应列表。

    返回:
        Dict[str, float]: 包含平均相关性、准确性和质量分数的字典。
    """
    # 初始化列表存储每个指标的分数
    relevance_scores: List[float] = []
    accuracy_scores: List[float] = []
    quality_scores: List[float] = []

    # 遍历每个查询及其对应的真实数据
    for query, ground_truth_chunk, ground_truth_response in zip(queries, ground_truth_chunks, ground_truth_responses):
        # 检索与查询相关的块
        retrieved_chunks: List[str] = retrieve_relevant_chunks(query)

        # 评估检索到的块与真实块的相关性
        relevance: float = evaluate_relevance(retrieved_chunks, [ground_truth_chunk])
        relevance_scores.append(relevance)

        # 使用基本的RAG管道生成响应
        response: str = basic_rag_pipeline(query)

        # 评估生成的响应与真实响应的准确性
        accuracy: float = evaluate_accuracy([response], [ground_truth_response])
        accuracy_scores.append(accuracy)

        # 评估生成的响应的质量
        quality: float = evaluate_response_quality([response])
        quality_scores.append(quality)

    # 计算每个指标的平均分数
    avg_relevance: float = np.mean(relevance_scores)
    avg_accuracy: float = np.mean(accuracy_scores)
    avg_quality: float = np.mean(quality_scores)

    # 以字典形式返回平均分数
    return {
        "average_relevance": avg_relevance,
        "average_accuracy": avg_accuracy,
        "average_quality": avg_quality
    }

# 打印一条消息，表示RAG管道的开始
print("🔍 运行检索增强生成（RAG）管道...")
print(f"📥 查询: {sample_query}\n")

# 运行RAG管道并获取响应
response = basic_rag_pipeline(sample_query)

# 以更好的格式打印响应
print("🤖 AI响应:")
print("-" * 50)
print(response.strip())
print("-" * 50)

# 打印真实答案以供比较
print("✅ 真实答案:")
print("-" * 50)
print(expected_answer)
print("-" * 50)

# 保存结果以便后续比较
results = {
    "query": query_text, # 输入的查询文本
    "ground_truth": expected_answer, # 查询的预期正确答案
    "simple_rag": {
        "response": simple_response, # 由简单RAG管道生成的响应
        "similarity": float(simple_sim) # 简单RAG响应与真实答案的相似度分数
        },
    "rl_rag": {
        "response": rl_response, # 由RL增强的RAG管道生成的响应
        "similarity": float(rl_sim) # RL增强的RAG响应与真实答案的相似度分数
        },
    "improvement": float(rl_sim - simple_sim) # RL增强的RAG相比简单RAG在相似度分数上的提升
}

# 将结果保存到JSON文件中，以便将来参考
with open('rl_rag_results.json', 'w') as f:
    json.dump(results, f, indent=2) # 将结果字典写入文件，并使用缩进以提高可读性

# 打印一条确认消息，表示结果已保存
print("\n结果已保存到rl_rag_results.json")


# 资料来源：https://github.com/FareedKhan-dev/all-rag-techniques.git


