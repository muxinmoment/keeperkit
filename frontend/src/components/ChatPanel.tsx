import { FormEvent, useState } from "react";

import { askRules, type Source } from "../api/rules";
import { SourceList } from "./SourceList";

type Message = {
  role: "user" | "assistant";
  content: string;
};

export function ChatPanel() {
  const [question, setQuestion] = useState("孤注一掷失败后会发生什么？");
  const [messages, setMessages] = useState<Message[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed) {
      return;
    }

    setIsLoading(true);
    setError(null);
    setMessages((current) => [...current, { role: "user", content: trimmed }]);

    try {
      const response = await askRules(trimmed);
      setMessages((current) => [...current, { role: "assistant", content: response.answer }]);
      setSources(response.sources);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unknown request error");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="shell">
      <section className="console">
        <div className="console__header">
          <div>
            <p className="eyebrow">KeeperKit Rules</p>
            <h1>守秘人的规则检索台</h1>
          </div>
          <span className="status">{isLoading ? "Consulting" : "Ready"}</span>
        </div>

        <div className="messages">
          {messages.length === 0 ? (
            <div className="empty">
              <p>把规则书放进后端数据目录，先让它成为一个靠谱的查书助手。</p>
            </div>
          ) : (
            messages.map((message, index) => (
              <article className={`message message--${message.role}`} key={`${message.role}-${index}`}>
                <span>{message.role === "user" ? "You" : "Oracle"}</span>
                <p>{message.content}</p>
              </article>
            ))
          )}
          {error ? <p className="error">{error}</p> : null}
        </div>

        <form className="prompt" onSubmit={handleSubmit}>
          <input
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="输入一个规则问题"
          />
          <button disabled={isLoading} type="submit">
            Ask
          </button>
        </form>
      </section>

      <SourceList sources={sources} />
    </main>
  );
}
