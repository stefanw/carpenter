Project = Backbone.Model.extend
  initialize: ->
    this.set 'files': new Files(this.get('files'))

File = Backbone.Model.extend
  initialize: ->
    this.set 'pages': new Pages(this.get('pages'))

Files = Backbone.Collection.extend
  model: File

Page = Backbone.Model.extend
  initialize: ->
    allImages.add this.get('images')
    this.set 'images': new Images this.get('images')

Pages = Backbone.Collection.extend
  model: Page

Image = Backbone.Model.extend
  initialize: ->
    this.set 'tables': new Tables this.get('tables')

Images = Backbone.Collection.extend
  model: Image

Table = Backbone.Model.extend
  initialize: ->
    this.set 'data': JSON.parse(this.get('data'))

Tables = Backbone.Collection.extend
  model: Table


ThumbnailListView = Backbone.View.extend
  tagName: 'ul'
  id: 'thumbnails'

  render: ()->
    @options.collection.each (li, i) =>
      @$el.append (new @options.itemClass
        item: li
        selected: li.id is @options.selected?.id
        number: i
      ).render()
    @$el


ThumbnailView = Backbone.View.extend
  tagName: "li"
  className: "thumbnail"

  render: ()->
    a = $('<a>',
        href: @getLink()
    )
    a.append $('<img>',
      src: Carpenter.options.static + @getImage()
    )
    if @options.selected
      @$el.addClass('selected')
    @$el.append(a)

PageThumbnailView = ThumbnailView.extend
  getImage: ()->
    @options.item.get('thumbnail')

  getLink: ()->
    "#file/#{@options.item.get('file')}/page/#{@options.item.id}"

ImageThumbnailView = ThumbnailView.extend
  getImage: ()->
    @options.item.get('path')

  getLink: ()->
    "#image/#{@options.item.id}"


PageView = Backbone.View.extend
  tagName: "div"
  className: "page"

  render: ()->
    @$el.append $('<img>',
      src: Carpenter.options.static + @options.page.get('image')
    )
    @options.page.get('images').each (img) ->

    @$el

ImageView = Backbone.View.extend
  tagName: "div"
  className: "image"

  render: ()->
    @$el.append $('<img>',
      src: Carpenter.options.static + @options.image.get('path')
    )

    @$el

ImageToolsView = Backbone.View.extend
  tagName: "div"
  className: "image-tools"

  events:
    'click .find-tables': 'findTables'
    'click .show-tables': 'showTables'

  findTables: (e) ->
    e.preventDefault()
    $.post("./image/#{@options.image.id}/analyze")

  showTables: (e) ->
    out = ''
    @options.image.get('tables').each (table) ->
      out += '<table class="table table-bordered">'
      for row in table.get('data')
        out += '<tr>'
        for cell in row
          if cell
            cell.colspan = cell.colspan or 1
            cell.rowspan = cell.rowspan or 1
            out += "<td rowspan='#{cell.rowspan}' colspan='#{cell.colspan}'>#{cell.text}</td>"
        out += '<tr>'
      out += '</table>'
    $('#page-container').html(out)

  render: () ->
    @$el.append $('<button>',
      'class': 'btn find-tables',
    ).text('Analyze')
    @$el.append $('<button>',
      'class': 'btn show-tables',
    ).text('Show Tables')
    @$el

allImages = new Images

ProjectRouter = Backbone.Router.extend
  initialize: (options) ->
    @project = new Project(options.project)

  routes:
    '':   'index'
    'file/:fileid':                'showFileFirstPage'
    'file/:fileid/page/:pageid':   'showPage'
    'image/:imageid':              'showImage'

  index: ->
    img = allImages.first()
    if img
      @navigate 'image/' + img.id, trigger: true

  showFileFirstPage: (fileid) ->
    file = @project.get('files').get fileid
    page = file.get('pages').first()
    Carpenter.router.navigate "file/#{file.id}/page/#{page.id}", trigger: true

  showPage: (fileid, pageid) ->
    file = @project.get('files').get(fileid)
    page = file.get('pages').get(pageid)
    thumbnails = new ThumbnailListView
      itemClass: PageThumbnailView
      collection: file.get('pages')
      selected: page
    $('#thumbnail-container').html thumbnails.render()
    pageView = new PageView page: page
    $('#page-container').html pageView.render()
    # $('#thumbnail-container').height $('#page-container').height()

  showImage: (imageid) ->
    img = allImages.get(imageid)
    thumbnails = new ThumbnailListView
      itemClass: ImageThumbnailView
      collection: allImages
      selected: img
    $('#thumbnail-container').html thumbnails.render()
    imageView = new ImageView image: img
    $('#page-container').html imageView.render()
    imageTools = new ImageToolsView image: img
    $('#tools-container').html imageTools.render()


window.Carpenter =
  setup: (project, @options) ->
    @router = new ProjectRouter(project: project)
    Backbone.history.start()
