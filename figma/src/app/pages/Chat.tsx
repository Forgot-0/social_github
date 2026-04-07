import { useEffect, useMemo, useRef, useState } from 'react';
import { ArrowLeft, Search, Send, MessageCircle, Circle, Plus, Loader2, X, UserRoundSearch, ChevronDown } from 'lucide-react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import { api } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';

type ChatListItem = {
  id: number;
  type: 'direct' | 'group' | 'channel';
  name?: string | null;
  description?: string | null;
  avatar_url?: string | null;
  last_activity_at?: string;
  unread_count?: number;
  member_count?: number;
  display_name?: string;
  other_user_id?: number | null;
  avatar?: string;
};

type ChatDetail = {
  id: number;
  type: 'direct' | 'group' | 'channel';
  name?: string | null;
  description?: string | null;
  avatar_url?: string | null;
  members: Array<{ user_id: number; role_id?: number; is_muted?: boolean }>;
  unread_count?: number;
};

type Message = {
  id: number;
  chat_id: number;
  author_id: number | null;
  type: string;
  content: string | null;
  created_at: string;
  updated_at?: string;
  is_deleted?: boolean;
  is_edited?: boolean;
};

function getAvatarUrl(avatars: any): string {
  if (!avatars || typeof avatars !== 'object') return '';
  const preferred = avatars['128'] || avatars['256'] || avatars.small || avatars.medium || avatars.large;
  if (typeof preferred === 'string') return preferred;
  if (preferred && typeof preferred === 'object' && 'url' in preferred) return String(preferred.url);
  const firstValue = Object.values(avatars)[0];
  if (typeof firstValue === 'string') return firstValue;
  if (firstValue && typeof firstValue === 'object' && 'url' in (firstValue as any)) return String((firstValue as any).url);
  return '';
}

function getInitial(value?: string) {
  return value?.trim()?.[0]?.toUpperCase() || 'Ч';
}

function getDisplayName(chat: ChatListItem | (ChatDetail & { display_name?: string }), currentUserId?: number) {
  if ((chat as any).display_name) return (chat as any).display_name as string;
  if (chat.name?.trim()) return chat.name;
  if (chat.type === 'direct') return currentUserId ? `Диалог #${currentUserId}` : 'Личный чат';
  return `Чат #${chat.id}`;
}

function normalize(value?: string | null) {
  return String(value || '').trim().toLowerCase();
}

function mergeProfileSearchResults(results: any[]) {
  const map = new Map<number, any>();
  results.forEach((result) => {
    const items = Array.isArray(result?.items) ? result.items : [];
    items.forEach((profile: any) => {
      if (typeof profile?.id === 'number' && !map.has(profile.id)) {
        map.set(profile.id, profile);
      }
    });
  });
  return Array.from(map.values());
}

function scoreProfile(profile: any, query: string) {
  const q = normalize(query);
  if (!q) return 0;

  const displayName = normalize(profile?.display_name);
  const specialization = normalize(profile?.specialization);
  const bio = normalize(profile?.bio);
  const skills = Array.isArray(profile?.skills) ? profile.skills.map((skill: string) => normalize(skill)) : [];

  let score = 0;
  if (displayName.startsWith(q)) score += 140;
  else if (displayName.includes(q)) score += 95;

  if (specialization.startsWith(q)) score += 70;
  else if (specialization.includes(q)) score += 45;

  skills.forEach((skill) => {
    if (skill === q) score += 90;
    else if (skill.startsWith(q)) score += 65;
    else if (skill.includes(q)) score += 40;
  });

  if (bio.includes(q)) score += 20;
  return score;
}

function highlightText(text: string, query: string) {
  if (!query.trim()) return text;
  const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp(`(${escaped})`, 'ig');
  const parts = text.split(regex);

  return parts.map((part, index) =>
    index % 2 === 1 ? (
      <mark key={`${part}-${index}`} className="rounded bg-primary/12 px-0.5 text-primary">
        {part}
      </mark>
    ) : (
      <span key={`${part}-${index}`}>{part}</span>
    )
  );
}

export function Chat() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [chats, setChats] = useState<ChatListItem[]>([]);
  const [selectedChat, setSelectedChat] = useState<(ChatListItem & { detail?: ChatDetail }) | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [messageInput, setMessageInput] = useState('');
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMoreChats, setHasMoreChats] = useState(false);
  const [loadingMoreChats, setLoadingMoreChats] = useState(false);
  const [showNewChat, setShowNewChat] = useState(false);
  const [profileSearchQuery, setProfileSearchQuery] = useState('');
  const [profileResults, setProfileResults] = useState<any[]>([]);
  const [searchingProfiles, setSearchingProfiles] = useState(false);
  const [creatingChat, setCreatingChat] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    void loadChats({ reset: true });
    connectWebSocket();

    return () => {
      disconnectWebSocket();
    };
  }, []);

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      void loadChats({ silent: true, reset: true });
      if (selectedChat?.id) {
        void loadMessages(selectedChat.id, { silent: true });
      }
    }, 15000);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [selectedChat?.id]);

  useEffect(() => {
    if (!selectedChat) return;
    void loadChatDetail(selectedChat.id);
    void loadMessages(selectedChat.id);
  }, [selectedChat?.id]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (!showNewChat) {
      setProfileSearchQuery('');
      setProfileResults([]);
      return;
    }

    const query = profileSearchQuery.trim();
    if (!query) {
      setProfileResults([]);
      return;
    }

    let cancelled = false;
    const timeoutId = window.setTimeout(async () => {
      try {
        setSearchingProfiles(true);
        const [byDisplayName, byUsername, bySkills] = await Promise.all([
          api.getProfiles({ display_name: query, page: 1, page_size: 8, sort: 'display_name:asc' }),
          api.getProfiles({ username: query, page: 1, page_size: 8, sort: 'display_name:asc' }),
          api.getProfiles({ skills: [query], page: 1, page_size: 8, sort: 'display_name:asc' }),
        ]);

        if (cancelled) return;

        const merged = mergeProfileSearchResults([byDisplayName, byUsername, bySkills])
          .filter((profile) => profile.id !== user?.id)
          .sort((left, right) => {
            const scoreDiff = scoreProfile(right, query) - scoreProfile(left, query);
            if (scoreDiff !== 0) return scoreDiff;
            return String(left.display_name || '').localeCompare(String(right.display_name || ''), 'ru');
          });

        setProfileResults(merged);
      } catch (error) {
        if (!cancelled) {
          console.error('Failed to search profiles for chat:', error);
          setProfileResults([]);
        }
      } finally {
        if (!cancelled) setSearchingProfiles(false);
      }
    }, 280);

    return () => {
      cancelled = true;
      window.clearTimeout(timeoutId);
    };
  }, [showNewChat, profileSearchQuery, user?.id]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const enrichChat = async (chat: any): Promise<ChatListItem> => {
    const base: ChatListItem = {
      id: chat.id,
      type: chat.type,
      name: chat.name,
      description: chat.description,
      avatar_url: chat.avatar_url,
      last_activity_at: chat.last_activity_at,
      unread_count: chat.unread_count || 0,
      member_count: chat.member_count || 0,
    };

    if (chat.type !== 'direct') {
      return { ...base, display_name: chat.name || `Чат #${chat.id}`, avatar: chat.avatar_url || '' };
    }

    try {
      const detail = await api.getChat(chat.id);
      const otherMember = Array.isArray(detail?.members)
        ? detail.members.find((member: any) => member.user_id !== user?.id)
        : null;

      if (!otherMember) {
        return { ...base, display_name: chat.name || `Чат #${chat.id}`, detail };
      }

      try {
        const profile = await api.getProfile(otherMember.user_id);
        return {
          ...base,
          detail,
          other_user_id: otherMember.user_id,
          display_name: profile?.display_name || chat.name || `Пользователь #${otherMember.user_id}`,
          avatar: getAvatarUrl(profile?.avatars),
          description: profile?.specialization || chat.description,
        };
      } catch {
        return {
          ...base,
          detail,
          other_user_id: otherMember.user_id,
          display_name: chat.name || `Пользователь #${otherMember.user_id}`,
        };
      }
    } catch {
      return { ...base, display_name: chat.name || `Чат #${chat.id}` };
    }
  };

  const loadChats = async ({ silent = false, reset = false, cursor }: { silent?: boolean; reset?: boolean; cursor?: string | null } = {}) => {
    try {
      if (!silent && reset) setLoading(true);
      if (cursor) setLoadingMoreChats(true);

      const data = await api.getChats({ limit: 20, cursor: cursor ?? undefined });
      const rawItems = Array.isArray(data?.items) ? data.items : [];
      const enriched = await Promise.all(rawItems.map((chat: any) => enrichChat(chat)));

      setChats((prev) => {
        const source = cursor ? [...prev, ...enriched] : enriched;
        const map = new Map<number, ChatListItem>();
        source.forEach((item) => map.set(item.id, item));
        return Array.from(map.values());
      });
      setNextCursor(data?.next_cursor || null);
      setHasMoreChats(Boolean(data?.has_more));

      if (selectedChat) {
        setSelectedChat((prev) => {
          if (!prev) return prev;
          const updated = enriched.find((chat) => chat.id === prev.id);
          return updated ? { ...prev, ...updated, detail: prev.detail } : prev;
        });
      }
    } catch (error: any) {
      console.error('Failed to load chats:', error);
      if (!silent) toast.error(error?.error?.message || 'Ошибка загрузки чатов');
      if (!cursor) setChats([]);
    } finally {
      if (!silent && reset) setLoading(false);
      if (cursor) setLoadingMoreChats(false);
    }
  };

  const loadChatDetail = async (chatId: number) => {
    try {
      const detail = await api.getChat(chatId);
      let displayName = detail?.name || undefined;
      let avatar = detail?.avatar_url || '';
      let description = detail?.description || undefined;
      let otherUserId: number | null = null;

      if (detail?.type === 'direct' && Array.isArray(detail?.members)) {
        const otherMember = detail.members.find((member: any) => member.user_id !== user?.id);
        if (otherMember) {
          otherUserId = otherMember.user_id;
          try {
            const profile = await api.getProfile(otherMember.user_id);
            displayName = profile?.display_name || displayName || `Пользователь #${otherMember.user_id}`;
            avatar = getAvatarUrl(profile?.avatars) || avatar;
            description = profile?.specialization || description;
          } catch {
            displayName = displayName || `Пользователь #${otherMember.user_id}`;
          }
        }
      }

      setSelectedChat((prev) => (prev && prev.id === chatId ? { ...prev, detail, display_name: displayName, avatar, description, other_user_id: otherUserId } : prev));
    } catch (error: any) {
      console.error('Failed to load chat detail:', error);
      toast.error(error?.error?.message || 'Ошибка загрузки чата');
    }
  };

  const loadMessages = async (chatId: number, { silent = false }: { silent?: boolean } = {}) => {
    try {
      const data = await api.getChatMessages(chatId, { limit: 100 });
      const items = Array.isArray(data?.items) ? data.items : [];
      const normalized = items
        .map((message: any) => ({
          id: message.id,
          chat_id: message.chat_id,
          author_id: message.author_id,
          type: message.type,
          content: message.content,
          created_at: message.created_at,
          updated_at: message.updated_at,
          is_deleted: message.is_deleted,
          is_edited: message.is_edited,
        }))
        .sort((a: Message, b: Message) => a.id - b.id);

      setMessages(normalized);

      const lastMessage = normalized[normalized.length - 1];
      if (lastMessage?.id) {
        await api.markMessagesRead(chatId, lastMessage.id);
      }
    } catch (error: any) {
      console.error('Failed to load messages:', error);
      if (!silent) toast.error(error?.error?.message || 'Ошибка загрузки сообщений');
      setMessages([]);
    }
  };

  const connectWebSocket = () => {
    try {
      const wsUrl = api.getWebSocketUrl();
      const ws = new WebSocket(wsUrl);

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data?.type === 'new_message') {
            if (typeof data?.payload?.id === 'number') {
              ws.send(
                JSON.stringify({
                  type: 'new_message',
                  chat_id: data.chat_id,
                  payload: { message_id: data.payload.id },
                  ts: '',
                })
              );
            }

            if (selectedChat && data.chat_id === selectedChat.id) {
              void loadMessages(selectedChat.id, { silent: true });
            }
            void loadChats({ silent: true, reset: true });
            return;
          }

          if (data?.type === 'message_edited' || data?.type === 'message_deleted') {
            if (selectedChat && data.chat_id === selectedChat.id) {
              void loadMessages(selectedChat.id, { silent: true });
            }
            return;
          }

          if (data?.type === 'messages_read') {
            void loadChats({ silent: true, reset: true });
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        window.setTimeout(() => {
          if (api.isAuthenticated()) connectWebSocket();
        }, 3000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  };

  const disconnectWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  };

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!messageInput.trim() || !selectedChat) return;

    const content = messageInput.trim();

    try {
      await api.sendMessage(selectedChat.id, { content, message_type: 'text' });
      setMessageInput('');
      await loadMessages(selectedChat.id, { silent: true });
      await loadChats({ silent: true, reset: true });
    } catch (error: any) {
      console.error('Failed to send message:', error);
      toast.error(error?.error?.message || 'Ошибка отправки сообщения');
    }
  };

  const findDirectChatForProfile = async (profileId: number) => {
    const data = await api.getChats({ limit: 100 });
    const rawItems = Array.isArray(data?.items) ? data.items : [];

    for (const rawChat of rawItems) {
      if (rawChat?.type !== 'direct') continue;
      try {
        const detail = await api.getChat(rawChat.id);
        const otherMember = Array.isArray(detail?.members)
          ? detail.members.find((member: any) => member.user_id !== user?.id)
          : null;
        if (otherMember?.user_id === profileId) {
          return enrichChat(rawChat);
        }
      } catch {
        // ignore and continue searching
      }
    }

    return null;
  };

  const createOrOpenDirectChat = async (profile: any) => {
    const existing = chats.find((chat) => chat.type === 'direct' && chat.other_user_id === profile.id);
    if (existing) {
      setSelectedChat(existing);
      setShowNewChat(false);
      return;
    }

    try {
      setCreatingChat(profile.id);
      const result = await api.createChat({
        chat_type: 'direct',
        member_ids: [profile.id],
      });

      setShowNewChat(false);
      setProfileSearchQuery('');
      setProfileResults([]);
      toast.success('Чат создан');

      let targetChat = null;
      if (result?.chat_id) {
        targetChat = await enrichChat({ id: result.chat_id, type: 'direct' });
      }
      if (!targetChat) {
        targetChat = await findDirectChatForProfile(profile.id);
      }

      await loadChats({ silent: true, reset: true });

      if (targetChat) {
        setChats((prev) => [targetChat!, ...prev.filter((item) => item.id !== targetChat!.id)]);
        setSelectedChat(targetChat);
      }
    } catch (error: any) {
      if (error?.error?.code === 'DIRECT_CHAT_EXISTS') {
        const existingChat = await findDirectChatForProfile(profile.id);
        if (existingChat) {
          setSelectedChat(existingChat);
          setChats((prev) => [existingChat!, ...prev.filter((item) => item.id !== existingChat!.id)]);
        }
        await loadChats({ silent: true, reset: true });
        setShowNewChat(false);
      } else {
        console.error('Failed to create direct chat:', error);
        toast.error(error?.error?.message || 'Не удалось создать чат');
      }
    } finally {
      setCreatingChat(null);
    }
  };

  const filteredChats = useMemo(() => {
    const query = searchQuery.toLowerCase();
    return chats.filter((chat) => {
      const haystack = `${chat.display_name || ''} ${chat.name || ''} ${chat.description || ''}`.toLowerCase();
      return haystack.includes(query);
    });
  }, [chats, searchQuery]);

  const formatTime = (dateString?: string) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'только что';
    if (diffMins < 60) return `${diffMins} мин`;
    if (diffHours < 24) return `${diffHours} ч`;
    if (diffDays < 7) return `${diffDays} д`;
    return date.toLocaleDateString('ru-RU');
  };

  const currentChatName = selectedChat ? getDisplayName(selectedChat as any, user?.id) : '';
  const currentChatAvatar = selectedChat?.avatar || selectedChat?.avatar_url || '';

  if (loading) {
    return (
      <div className="py-20 text-center">
        <div className="inline-block h-12 w-12 animate-spin rounded-full border-b-2 border-primary"></div>
        <p className="mt-4 text-muted-foreground">Загрузка чатов...</p>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-4rem)]">
      <div className="mx-auto h-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <div className="flex h-full flex-col overflow-hidden rounded-xl border border-border bg-white shadow-sm lg:flex-row">
          <div className={`flex flex-col border-r border-border lg:w-1/3 ${selectedChat ? 'hidden lg:flex' : 'flex'}`}>
            <div className="border-b border-border p-4">
              <div className="mb-4 flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-xl font-semibold">Сообщения</h2>
                  <p className="text-sm text-muted-foreground">Личные и групповые чаты</p>
                </div>
                <button
                  type="button"
                  onClick={() => setShowNewChat((prev) => !prev)}
                  className="inline-flex items-center gap-2 rounded-xl border border-primary/15 bg-primary/5 px-3 py-2 text-sm font-medium text-primary transition-colors hover:bg-primary/10"
                >
                  {showNewChat ? <X className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
                  <span>{showNewChat ? 'Скрыть' : 'Новый чат'}</span>
                </button>
              </div>

              {showNewChat ? (
                <div className="mb-4 rounded-2xl border border-border bg-secondary/35 p-3">
                  <div className="mb-3 flex items-center gap-2 text-sm font-medium text-foreground">
                    <UserRoundSearch className="h-4 w-4 text-primary" />
                    Поиск профиля для нового диалога
                  </div>
                  <div className="relative">
                    <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <input
                      type="text"
                      placeholder="Имя, стек или навык"
                      value={profileSearchQuery}
                      onChange={(e) => setProfileSearchQuery(e.target.value)}
                      className="app-input w-full pl-10 pr-4"
                    />
                  </div>

                  <div className="mt-3 max-h-72 overflow-y-auto">
                    {searchingProfiles ? (
                      <div className="flex items-center gap-2 px-2 py-3 text-sm text-muted-foreground">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Ищем профили...
                      </div>
                    ) : profileSearchQuery.trim() && profileResults.length === 0 ? (
                      <div className="px-2 py-3 text-sm text-muted-foreground">Ничего не найдено</div>
                    ) : (
                      <div className="space-y-2">
                        {profileResults.map((profile) => {
                          const displayName = profile.display_name || `Профиль #${profile.id}`;
                          const avatarUrl = getAvatarUrl(profile);
                          const existingDirectChat = chats.find((chat) => chat.type === 'direct' && chat.other_user_id === profile.id);
                          return (
                            <button
                              key={profile.id}
                              type="button"
                              onClick={() => void createOrOpenDirectChat(profile)}
                              disabled={creatingChat === profile.id}
                              className="flex w-full items-start gap-3 rounded-2xl border border-border bg-white px-3 py-3 text-left transition-colors hover:border-primary/30 hover:bg-primary/5 disabled:cursor-not-allowed disabled:opacity-70"
                            >
                              <Avatar className="h-11 w-11 shrink-0 ring-1 ring-primary/10">
                                <AvatarImage src={avatarUrl} alt={displayName} className="object-cover" />
                                <AvatarFallback className="bg-primary text-white font-semibold">
                                  {getInitial(displayName)}
                                </AvatarFallback>
                              </Avatar>
                              <div className="min-w-0 flex-1">
                                <div className="truncate font-medium text-foreground">{highlightText(displayName, profileSearchQuery)}</div>
                                <div className="mt-1 truncate text-sm text-muted-foreground">
                                  {profile.specialization ? highlightText(profile.specialization, profileSearchQuery) : `ID профиля: ${profile.id}`}
                                </div>
                                {Array.isArray(profile.skills) && profile.skills.length > 0 ? (
                                  <div className="mt-2 flex flex-wrap gap-1.5">
                                    {profile.skills.slice(0, 4).map((skill: string) => (
                                      <span key={skill} className="rounded-full bg-secondary px-2 py-1 text-[11px] text-secondary-foreground">
                                        {highlightText(skill, profileSearchQuery)}
                                      </span>
                                    ))}
                                  </div>
                                ) : null}
                              </div>
                              <span className="inline-flex items-center gap-1 rounded-full bg-primary/8 px-2 py-1 text-[11px] font-medium text-primary">
                                {creatingChat === profile.id ? <Loader2 className="h-3 w-3 animate-spin" /> : <MessageCircle className="h-3 w-3" />}
                                {creatingChat === profile.id ? 'создаём' : existingDirectChat ? 'открыть чат' : 'написать'}
                              </span>
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>
              ) : null}

              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Поиск чатов..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="app-input w-full pl-10 pr-4 py-2"
                />
              </div>
            </div>

            <div className="flex-1 overflow-y-auto">
              {filteredChats.length === 0 ? (
                <div className="p-8 text-center text-muted-foreground">
                  <p>Нет активных чатов</p>
                  <p className="mt-2 text-sm">Открой новый диалог через поиск профиля</p>
                </div>
              ) : (
                <>
                  {filteredChats.map((chat) => (
                    <button
                      key={chat.id}
                      onClick={() => setSelectedChat(chat)}
                      className={`w-full border-b border-border p-4 text-left transition-colors hover:bg-secondary/50 ${
                        selectedChat?.id === chat.id ? 'bg-secondary' : ''
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <Avatar className="h-12 w-12 shrink-0">
                          <AvatarImage src={chat.avatar || chat.avatar_url || ''} alt={chat.display_name || chat.name || `Чат #${chat.id}`} className="object-cover" />
                          <AvatarFallback className="bg-primary text-white font-semibold">
                            {getInitial(chat.display_name || chat.name || 'Ч')}
                          </AvatarFallback>
                        </Avatar>
                        <div className="min-w-0 flex-1">
                          <div className="mb-1 flex items-center justify-between gap-3">
                            <h3 className="truncate font-semibold">{chat.display_name || chat.name || `Чат #${chat.id}`}</h3>
                            {chat.last_activity_at ? (
                              <span className="whitespace-nowrap text-xs text-muted-foreground">{formatTime(chat.last_activity_at)}</span>
                            ) : null}
                          </div>
                          <p className="truncate text-sm text-muted-foreground">
                            {chat.description || (chat.type === 'direct' ? 'Личный диалог' : 'Групповой чат')}
                          </p>
                        </div>
                        {(chat.unread_count || 0) > 0 && (
                          <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-semibold text-white">
                            {chat.unread_count}
                          </div>
                        )}
                      </div>
                    </button>
                  ))}

                  {hasMoreChats ? (
                    <div className="p-4">
                      <button
                        type="button"
                        onClick={() => void loadChats({ cursor: nextCursor })}
                        disabled={loadingMoreChats || !nextCursor}
                        className="inline-flex w-full items-center justify-center gap-2 rounded-xl border border-border px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {loadingMoreChats ? <Loader2 className="h-4 w-4 animate-spin" /> : <ChevronDown className="h-4 w-4" />}
                        {loadingMoreChats ? 'Загрузка...' : 'Показать ещё'}
                      </button>
                    </div>
                  ) : null}
                </>
              )}
            </div>
          </div>

          {selectedChat ? (
            <div className="flex flex-1 flex-col">
              <div className="flex items-center space-x-3 border-b border-border p-4">
                <button onClick={() => setSelectedChat(null)} className="rounded-lg p-2 hover:bg-secondary lg:hidden">
                  <ArrowLeft className="h-5 w-5" />
                </button>
                <Avatar className="h-10 w-10">
                  <AvatarImage src={currentChatAvatar} alt={currentChatName} className="object-cover" />
                  <AvatarFallback className="bg-primary text-white font-semibold">
                    {getInitial(currentChatName)}
                  </AvatarFallback>
                </Avatar>
                <div className="min-w-0 flex-1">
                  <h3 className="truncate font-semibold">{currentChatName}</h3>
                  <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                    <span className="inline-flex items-center gap-1">
                      <Circle className="h-2 w-2 fill-green-500 text-green-500" />
                      {selectedChat.detail?.type === 'direct' ? 'личный чат' : 'чат активен'}
                    </span>
                    {selectedChat.other_user_id ? (
                      <Link to={`/profiles/${selectedChat.other_user_id}`} className="text-primary hover:underline">
                        открыть профиль
                      </Link>
                    ) : null}
                  </div>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 ? (
                  <div className="flex h-full items-center justify-center text-muted-foreground">
                    <div className="text-center">
                      <MessageCircle className="mx-auto mb-4 h-14 w-14 opacity-20" />
                      <p>Сообщений пока нет</p>
                    </div>
                  </div>
                ) : (
                  messages.map((message) => {
                    const isOwn = message.author_id === user?.id;
                    return (
                      <div key={message.id} className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}>
                        <div
                          className={`max-w-[75%] rounded-2xl px-4 py-3 ${
                            isOwn ? 'bg-primary text-white' : 'bg-secondary text-secondary-foreground'
                          }`}
                        >
                          <p className="break-words">{message.is_deleted ? 'Сообщение удалено' : message.content || 'Без текста'}</p>
                          <div className="mt-1 flex items-center justify-end space-x-1">
                            <span className={`text-xs ${isOwn ? 'text-white/70' : 'text-muted-foreground'}`}>
                              {formatTime(message.created_at)}
                            </span>
                            {message.is_edited ? (
                              <span className={`text-xs ${isOwn ? 'text-white/70' : 'text-muted-foreground'}`}>(изм.)</span>
                            ) : null}
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
                <div ref={messagesEndRef} />
              </div>

              <form onSubmit={sendMessage} className="border-t border-border p-4">
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={messageInput}
                    onChange={(e) => setMessageInput(e.target.value)}
                    placeholder="Введите сообщение..."
                    className="flex-1 rounded-lg border border-border px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                  <button
                    type="submit"
                    disabled={!messageInput.trim()}
                    className="flex items-center space-x-2 rounded-lg bg-primary px-6 py-3 text-white transition-colors hover:bg-accent disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <Send className="h-5 w-5" />
                  </button>
                </div>
              </form>
            </div>
          ) : (
            <div className="hidden flex-1 items-center justify-center text-muted-foreground lg:flex">
              <div className="text-center">
                <MessageCircle className="mx-auto mb-4 h-16 w-16 opacity-20" />
                <p className="text-lg">Выберите чат для начала общения</p>
                <p className="mt-2 text-sm">Или откройте новый диалог через поиск профиля</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
