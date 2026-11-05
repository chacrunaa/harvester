import type { Message } from '../../entity';

type Props = { message: Extract<Message, { type: 'agent-card' }> };

export const AgentCard = ({ message }: Props) => {
  const { agentTitle, summary } = message.content;
  return (
    <div data-message-type="agent-card">
      <strong>{agentTitle}</strong>
      <p>{summary}</p>
    </div>
  );
};
