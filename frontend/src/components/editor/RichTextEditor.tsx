'use client'
import { useCallback, useRef } from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Image from '@tiptap/extension-image'
import Link from '@tiptap/extension-link'
import Underline from '@tiptap/extension-underline'
import TextAlign from '@tiptap/extension-text-align'
import Placeholder from '@tiptap/extension-placeholder'
import api from '@/lib/api'
import {
  Bold, Italic, UnderlineIcon, List, ListOrdered, Quote, Code,
  Heading2, Heading3, AlignLeft, AlignCenter, AlignRight, Link2, ImagePlus,
} from 'lucide-react'

async function uploadImage(file: File): Promise<string> {
  const form = new FormData()
  form.append('image', file)
  const res = await api.post('/api/v1/intra/upload/', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  const url: string = res.data.url
  return url.startsWith('http') ? url : `http://localhost:8000${url}`
}

function ToolbarBtn({
  onClick, active, title, children,
}: { onClick: () => void; active?: boolean; title: string; children: React.ReactNode }) {
  return (
    <button
      type="button"
      onMouseDown={(e) => { e.preventDefault(); onClick() }}
      title={title}
      className={`p-1.5 rounded transition-colors ${
        active ? 'bg-gray-700 text-white' : 'text-gray-300 hover:bg-gray-600 hover:text-white'
      }`}
    >
      {children}
    </button>
  )
}

interface Props {
  content: string
  onChange: (html: string) => void
}

export default function RichTextEditor({ content, onChange }: Props) {
  const fileRef = useRef<HTMLInputElement>(null)

  const editor = useEditor({
    extensions: [
      StarterKit,
      Underline,
      Image.configure({ inline: false, allowBase64: false }),
      Link.configure({ openOnClick: false }),
      TextAlign.configure({ types: ['heading', 'paragraph'] }),
      Placeholder.configure({ placeholder: '本文を入力してください...' }),
    ],
    content,
    onUpdate: ({ editor }) => onChange(editor.getHTML()),
    editorProps: {
      attributes: {
        class: 'outline-none min-h-[300px] prose prose-sm max-w-none prose-invert',
      },
    },
  })

  const handleImageUpload = useCallback(async (file: File) => {
    try {
      const url = await uploadImage(file)
      editor?.chain().focus().setImage({ src: url }).run()
    } catch {
      alert('画像のアップロードに失敗しました')
    }
  }, [editor])

  const handlePaste = useCallback(async (e: React.ClipboardEvent) => {
    const items = Array.from(e.clipboardData.items)
    const imageItem = items.find((item) => item.type.startsWith('image/'))
    if (imageItem) {
      e.preventDefault()
      const file = imageItem.getAsFile()
      if (file) await handleImageUpload(file)
    }
  }, [handleImageUpload])

  const setLink = useCallback(() => {
    const url = window.prompt('URLを入力してください')
    if (!url) return
    editor?.chain().focus().setLink({ href: url }).run()
  }, [editor])

  if (!editor) return (
    <div className="flex-1 flex items-center justify-center bg-gray-800 border border-gray-600 rounded-lg text-gray-500 text-sm">
      エディタを読み込み中...
    </div>
  )

  return (
    <div className="flex flex-col flex-1 min-h-0 border border-gray-600 rounded-lg overflow-hidden">
      {/* ツールバー */}
      <div className="flex flex-wrap gap-0.5 px-2 py-1.5 bg-gray-700 border-b border-gray-600 shrink-0">
        <ToolbarBtn onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
          active={editor.isActive('heading', { level: 2 })} title="見出し2">
          <Heading2 size={15} />
        </ToolbarBtn>
        <ToolbarBtn onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
          active={editor.isActive('heading', { level: 3 })} title="見出し3">
          <Heading3 size={15} />
        </ToolbarBtn>
        <div className="w-px bg-gray-600 mx-1" />
        <ToolbarBtn onClick={() => editor.chain().focus().toggleBold().run()}
          active={editor.isActive('bold')} title="太字">
          <Bold size={15} />
        </ToolbarBtn>
        <ToolbarBtn onClick={() => editor.chain().focus().toggleItalic().run()}
          active={editor.isActive('italic')} title="斜体">
          <Italic size={15} />
        </ToolbarBtn>
        <ToolbarBtn onClick={() => editor.chain().focus().toggleUnderline().run()}
          active={editor.isActive('underline')} title="下線">
          <UnderlineIcon size={15} />
        </ToolbarBtn>
        <div className="w-px bg-gray-600 mx-1" />
        <ToolbarBtn onClick={() => editor.chain().focus().toggleBulletList().run()}
          active={editor.isActive('bulletList')} title="箇条書き">
          <List size={15} />
        </ToolbarBtn>
        <ToolbarBtn onClick={() => editor.chain().focus().toggleOrderedList().run()}
          active={editor.isActive('orderedList')} title="番号付きリスト">
          <ListOrdered size={15} />
        </ToolbarBtn>
        <ToolbarBtn onClick={() => editor.chain().focus().toggleBlockquote().run()}
          active={editor.isActive('blockquote')} title="引用">
          <Quote size={15} />
        </ToolbarBtn>
        <ToolbarBtn onClick={() => editor.chain().focus().toggleCodeBlock().run()}
          active={editor.isActive('codeBlock')} title="コードブロック">
          <Code size={15} />
        </ToolbarBtn>
        <div className="w-px bg-gray-600 mx-1" />
        <ToolbarBtn onClick={() => editor.chain().focus().setTextAlign('left').run()}
          active={editor.isActive({ textAlign: 'left' })} title="左揃え">
          <AlignLeft size={15} />
        </ToolbarBtn>
        <ToolbarBtn onClick={() => editor.chain().focus().setTextAlign('center').run()}
          active={editor.isActive({ textAlign: 'center' })} title="中央揃え">
          <AlignCenter size={15} />
        </ToolbarBtn>
        <ToolbarBtn onClick={() => editor.chain().focus().setTextAlign('right').run()}
          active={editor.isActive({ textAlign: 'right' })} title="右揃え">
          <AlignRight size={15} />
        </ToolbarBtn>
        <div className="w-px bg-gray-600 mx-1" />
        <ToolbarBtn onClick={setLink} active={editor.isActive('link')} title="リンク">
          <Link2 size={15} />
        </ToolbarBtn>
        <ToolbarBtn onClick={() => fileRef.current?.click()} title="画像を挿入">
          <ImagePlus size={15} />
        </ToolbarBtn>
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => { if (e.target.files?.[0]) handleImageUpload(e.target.files[0]) }}
        />
      </div>

      {/* エディタ本体 */}
      <div className="flex-1 overflow-y-auto bg-gray-800 p-4" onPaste={handlePaste}>
        <EditorContent editor={editor} />
      </div>
    </div>
  )
}
