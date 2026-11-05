import type { Message } from '../../entity';

type Props = { message: Extract<Message, { type: 'user' }> };

export const UserMessage = ({ message }: Props) => (
  <div data-message-type="user">{message.content}</div>
);
