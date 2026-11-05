import type { Message } from '../../entity';

type Props = { message: Extract<Message, { type: 'system' }> };

export const SystemMessage = ({ message }: Props) => (
  <div data-message-type="system">{message.content}</div>
);
