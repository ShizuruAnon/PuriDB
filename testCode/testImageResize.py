import wx

class MainPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, style=wx.FULL_REPAINT_ON_RESIZE)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.img = wx.Image('background.png', wx.BITMAP_TYPE_ANY)
        self.imgx, self.imgy = self.img.GetSize()

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        #dc.Clear()
        x,y = self.GetSize()
        posx,posy = 0, 0
        newy = int(float(x)/self.imgx*self.imgy)
        if newy < y:
            posy = int((y - newy) / 2) 
            y = newy
        else:
            newx = int(float(y)/self.imgy*self.imgx)
            posx = int((x - newx) / 2)
            x = newx        

        img = self.img.Scale(x,y, wx.IMAGE_QUALITY_HIGH)
        self.bmp = wx.BitmapFromImage(img)
        dc.DrawBitmap(self.bmp,posx,posy)

class MainFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, title='Test', size=(600,400))
        self.panel = MainPanel(self)
        self.Show()

app = wx.App(0)
frame = MainFrame(None)
app.MainLoop()    