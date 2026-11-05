import type { Message } from '../../entity';

type Props = { message: Extract<Message, { type: 'qna-form' }> };

export const QnaForm = ({ message }: Props) => {
  const { agentId, questions } = message.content;
  return (
    <div data-message-type="qna-form">
      <header>{agentId}</header>
      <ul>
        {questions.map((q) => (
          <li key={q.id}>{q.text}</li>
        ))}
      </ul>
    </div>
  );
};
