--[[ fit_base.lua -- Studio command bar, Edit mode.  Safe to re-run.

ONE-TIME SETUP
 1. 3D Importer: import military_base.fbx. It lands in Workspace as a Model (default name "military_base").
 2. ServerStorage: add a ModuleScript named BaseData and paste base_data.lua into it.
 3. Optional makers: import makers.fbx (Model "makers") and add ModuleScript ServerStorage.MakersData
    with makers_data.lua.
 4. Paste this whole file into the command bar and press Enter.

WHAT IT DOES
 * Scales/moves the imported base so 1 stud = 1 stud and the base origin (ground centre, +Z = gate) is at
   the world origin; checks the gate really is at +Z and the hangar at +X.
 * Colours parts from the name suffix (Group_Material), turns mesh collision OFF, and builds invisible
   collision Parts, ladder TrussParts and PointLights from BaseData.
 * Saves ServerStorage.MilitaryBaseTemplate and puts a copy on every plot in Workspace.Plots.
 * Splits the makers import into ServerStorage.Makers.<Name> models, anchored, pivot at bottom centre.

Collision choice: visual meshes never collide; every walkable surface/wall is an exact invisible box Part
generated from BaseData, because cheap Box collision is exact for boxes and no decomposition cost is paid.
]]

local CONFIG = {
	BASE_IMPORT = "military_base",
	MAKERS_IMPORT = "makers",
	PLOTS = "Plots",               -- Workspace folder: one child per plot (a floor Part, or a Model containing one)
	BASE_NAME = "MilitaryBase",
	LIGHT_RANGE = 22,
	LIGHT_BRIGHTNESS = 1.4,
}

-- suffix -> {Color3, Material}; keep in sync with PALETTE in blocks.py
local STYLE = {
	Olive        = {Color3.fromRGB(92, 104, 62),   Enum.Material.SmoothPlastic},
	DarkOlive    = {Color3.fromRGB(60, 68, 44),    Enum.Material.SmoothPlastic},
	Concrete     = {Color3.fromRGB(170, 166, 152), Enum.Material.Concrete},
	DarkConcrete = {Color3.fromRGB(112, 110, 102), Enum.Material.Concrete},
	Asphalt      = {Color3.fromRGB(50, 52, 55),    Enum.Material.Asphalt},
	Metal        = {Color3.fromRGB(92, 96, 100),   Enum.Material.Metal},
	Steel        = {Color3.fromRGB(150, 154, 158), Enum.Material.DiamondPlate},
	Hazard       = {Color3.fromRGB(224, 178, 40),  Enum.Material.SmoothPlastic},
	Marking      = {Color3.fromRGB(228, 224, 208), Enum.Material.SmoothPlastic},
	Sand         = {Color3.fromRGB(178, 158, 114), Enum.Material.Sand},
	Wood         = {Color3.fromRGB(122, 92, 60),   Enum.Material.WoodPlanks},
	Canvas       = {Color3.fromRGB(130, 122, 90),  Enum.Material.Fabric},
	Rust         = {Color3.fromRGB(128, 70, 44),   Enum.Material.CorrodedMetal},
	Black        = {Color3.fromRGB(24, 24, 26),    Enum.Material.SmoothPlastic},
	Glass        = {Color3.fromRGB(150, 190, 210), Enum.Material.Glass},
	Lamp         = {Color3.fromRGB(255, 236, 180), Enum.Material.Neon},
	Beacon       = {Color3.fromRGB(255, 44, 32),   Enum.Material.Neon},
	Shady        = {Color3.fromRGB(150, 60, 255),  Enum.Material.Neon},
}
local LIGHT_COLOR = {
	Lamp = Color3.fromRGB(255, 226, 170),
	Beacon = Color3.fromRGB(255, 50, 30),
	Shady = Color3.fromRGB(160, 70, 255),
}

local ServerStorage = game:GetService("ServerStorage")
local CHS = game:GetService("ChangeHistoryService")

local function log(...) print("[FIT]", ...) end
local function v3(t) return Vector3.new(t[1], t[2], t[3]) end
local function suffix(name) return name:match("_(%a+)$") end

local function aabb(model)
	local lo, hi = Vector3.new(math.huge, math.huge, math.huge), Vector3.new(-math.huge, -math.huge, -math.huge)
	local n = 0
	for _, p in ipairs(model:GetDescendants()) do
		if p:IsA("BasePart") then
			n += 1
			local cf, h = p.CFrame, p.Size / 2
			for _, sx in ipairs({-1, 1}) do
				for _, sy in ipairs({-1, 1}) do
					for _, sz in ipairs({-1, 1}) do
						local w = cf * Vector3.new(sx * h.X, sy * h.Y, sz * h.Z)
						lo = Vector3.new(math.min(lo.X, w.X), math.min(lo.Y, w.Y), math.min(lo.Z, w.Z))
						hi = Vector3.new(math.max(hi.X, w.X), math.max(hi.Y, w.Y), math.max(hi.Z, w.Z))
					end
				end
			end
		end
	end
	return lo, hi, n
end

-- Scale + translate an import so its bounding box matches the generator's bbox exactly.
local function fitToData(model, data)
	local eMin, eMax = v3(data.bboxMin), v3(data.bboxMax)
	local eSize = eMax - eMin
	local lo, hi = aabb(model)
	local size = hi - lo
	log(string.format("%s imported size %.2f x %.2f x %.2f (expected %.2f x %.2f x %.2f)",
		model.Name, size.X, size.Y, size.Z, eSize.X, eSize.Y, eSize.Z))
	local f = eSize.X / size.X
	if math.abs(f - 1) > 1e-3 then
		model:ScaleTo(model:GetScale() * f)
		log(string.format("  scaled by %.4f", f))
		lo, hi = aabb(model)
		size = hi - lo
	end
	for _, ax in ipairs({"X", "Y", "Z"}) do
		if math.abs(size[ax] - eSize[ax]) > 0.05 * math.max(1, eSize[ax]) then
			warn(string.format("[FIT]   %s axis is %.2f, expected %.2f - was the FBX imported with a different up/forward axis?",
				ax, size[ax], eSize[ax]))
		end
	end
	model:PivotTo(model:GetPivot() + (eMin - lo))
	model.WorldPivot = CFrame.new()
end

local function avgPos(model, prefix)
	local s, n = Vector3.zero, 0
	for _, p in ipairs(model:GetDescendants()) do
		if p:IsA("BasePart") and p.Name:sub(1, #prefix) == prefix then
			s += p.Position
			n += 1
		end
	end
	return n > 0 and s / n or nil
end

local function style(model)
	local lights, unknown, meshes = 0, {}, 0
	for _, p in ipairs(model:GetDescendants()) do
		if p:IsA("BasePart") then
			meshes += 1
			local suf = suffix(p.Name)
			local st = suf and STYLE[suf]
			p.Anchored = true
			p.CanCollide = false
			p.CanTouch = false
			p.CanQuery = false
			if p:IsA("MeshPart") then
				p.CollisionFidelity = Enum.CollisionFidelity.Box
				p.RenderFidelity = Enum.RenderFidelity.Automatic
				pcall(function() p.TextureID = "" end)
			end
			if st then
				p.Color, p.Material = st[1], st[2]
				p.Transparency = (suf == "Glass") and 0.45 or 0
				p.CastShadow = not (suf == "Glass" or LIGHT_COLOR[suf])
				p.Reflectance = 0
				if LIGHT_COLOR[suf] and not p:FindFirstChildOfClass("PointLight") then
					local L = Instance.new("PointLight")
					L.Color = LIGHT_COLOR[suf]
					L.Range = suf == "Lamp" and CONFIG.LIGHT_RANGE or 16
					L.Brightness = CONFIG.LIGHT_BRIGHTNESS
					L.Shadows = false
					L.Parent = p
					lights += 1
				end
			else
				unknown[suf or p.Name] = true
			end
		end
	end
	for k in pairs(unknown) do warn("[FIT] no style for suffix/name:", k) end
	return meshes, lights
end

local function buildCollision(parent, list, offset)
	local folder = Instance.new("Folder")
	folder.Name = "Collision"
	for _, c in ipairs(list) do
		local p = Instance.new("Part")
		p.Name = "C"
		p.Anchored = true
		p.CanCollide = true
		p.CanTouch = false
		p.CanQuery = true
		p.CastShadow = false
		p.Transparency = 1
		p.Material = Enum.Material.SmoothPlastic
		p.Size = Vector3.new(c[4], c[5], c[6])
		p.CFrame = CFrame.new(offset + Vector3.new(c[1], c[2], c[3]))
		p.Parent = folder
	end
	folder.Parent = parent
	return #list
end

local function buildTrusses(parent, list)
	local folder = Instance.new("Folder")
	folder.Name = "Ladders"
	for _, t in ipairs(list) do
		local p = Instance.new("TrussPart")
		p.Name = "Ladder"
		p.Anchored = true
		p.Transparency = 1
		p.Style = Enum.Style.NoSupports
		p.Size = Vector3.new(2, t[4], 2)
		p.CFrame = CFrame.new(t[1], t[2] + t[4] / 2, t[3])
		p.Parent = folder
	end
	folder.Parent = parent
	return #list
end

local function plotFloor(plot)
	if plot:IsA("BasePart") then return plot end
	if plot:IsA("Model") and plot.PrimaryPart then return plot.PrimaryPart end
	local named = plot:FindFirstChild("Floor", true)
	if named and named:IsA("BasePart") then return named end
	local best, area = nil, 0
	for _, d in ipairs(plot:GetDescendants()) do
		if d:IsA("BasePart") and d.Size.X * d.Size.Z > area then best, area = d, d.Size.X * d.Size.Z end
	end
	return best
end

-------------------------------------------------------------------- base
local function doBase()
	local mod = ServerStorage:FindFirstChild("BaseData")
	if not mod then warn("[FIT] ServerStorage.BaseData missing - paste base_data.lua into a ModuleScript") return end
	local okc, data = pcall(require, mod:Clone())   -- clone so edits to the module are always picked up
	if not okc then data = require(mod) end
	local import = workspace:FindFirstChild(CONFIG.BASE_IMPORT)
	local template = ServerStorage:FindFirstChild("MilitaryBaseTemplate")
	if import then
		if template then template:Destroy() end
		fitToData(import, data)
		-- orientation sanity: gate must be at +Z, hangar at +X
		local gate, hangar = avgPos(import, "Gate"), avgPos(import, "Hangar")
		if gate and gate.Z < 0 then
			warn("[FIT] gate came in at -Z: rotating the import 180 degrees")
			import:PivotTo(CFrame.Angles(0, math.pi, 0) * import:GetPivot())
			hangar = avgPos(import, "Hangar")
		end
		if hangar and hangar.X < 0 then
			warn("[FIT] hangar is at -X: the FBX looks mirrored. Re-export with axis_forward=-Z, axis_up=Y.")
		end
		local meshes, lights = style(import)
		local nc = buildCollision(import, data.collision, Vector3.zero)
		local nt = buildTrusses(import, data.trusses)
		import.Name = "MilitaryBaseTemplate"
		import.Parent = ServerStorage
		template = import
		log(string.format("template built: %d meshes, %d lights, %d collision parts, %d ladders", meshes, lights, nc, nt))
	elseif template then
		log("no new import found - re-using ServerStorage.MilitaryBaseTemplate")
	else
		warn("[FIT] nothing to do: import military_base.fbx first")
		return
	end

	local plots = workspace:FindFirstChild(CONFIG.PLOTS)
	if not plots then
		warn("[FIT] Workspace." .. CONFIG.PLOTS .. " not found - placing one copy at the origin for testing")
		local old = workspace:FindFirstChild(CONFIG.BASE_NAME)
		if old then old:Destroy() end
		local c = template:Clone()
		c.Name = CONFIG.BASE_NAME
		c.Parent = workspace
		return
	end
	local placed = 0
	for _, plot in ipairs(plots:GetChildren()) do
		local floor = plotFloor(plot)
		if not floor then
			warn("[FIT] no floor part found in plot", plot:GetFullName())
		else
			local holder = plot:IsA("BasePart") and plots or plot
			local name = plot:IsA("BasePart") and (CONFIG.BASE_NAME .. "_" .. plot.Name) or CONFIG.BASE_NAME
			local old = holder:FindFirstChild(name)
			if old then old:Destroy() end
			local c = template:Clone()
			c.Name = name
			c:PivotTo(floor.CFrame * CFrame.new(0, floor.Size.Y / 2, 0))
			c.Parent = holder
			placed += 1
			if math.abs(floor.Size.X - 400) > 1 or math.abs(floor.Size.Z - 400) > 1 then
				warn(string.format("[FIT] plot %s floor is %.0f x %.0f, base expects 400 x 400", plot.Name, floor.Size.X, floor.Size.Z))
			end
		end
	end
	log("placed on", placed, "plot(s)")
end

-------------------------------------------------------------------- makers
local function doMakers()
	local mod = ServerStorage:FindFirstChild("MakersData")
	local import = workspace:FindFirstChild(CONFIG.MAKERS_IMPORT)
	if not (mod and import) then
		log("makers skipped (need Workspace." .. CONFIG.MAKERS_IMPORT .. " and ServerStorage.MakersData)")
		return
	end
	local okc, data = pcall(require, mod:Clone())
	if not okc then data = require(mod) end
	fitToData(import, data)
	style(import)
	local folder = ServerStorage:FindFirstChild("Makers") or Instance.new("Folder")
	folder.Name = "Makers"
	folder.Parent = ServerStorage
	for _, mk in ipairs(data.makers) do
		local old = folder:FindFirstChild(mk.name)
		if old then old:Destroy() end
		local model = Instance.new("Model")
		model.Name = mk.name
		local origin = v3(mk.origin)
		local n = 0
		for _, p in ipairs(import:GetDescendants()) do
			if p:IsA("BasePart") and p.Name:sub(1, #mk.name) == mk.name then
				p.Parent = model
				n += 1
			end
		end
		buildCollision(model, mk.collision, origin)
		local root = Instance.new("Part")
		root.Name = "Root"
		root.Anchored = true
		root.CanCollide = false
		root.CanTouch = false
		root.CanQuery = false
		root.Transparency = 1
		root.Size = Vector3.new(24, 1, 24)
		root.CFrame = CFrame.new(origin + Vector3.new(0, 0.5, 0))
		root.Parent = model
		model.PrimaryPart = root
		model.WorldPivot = CFrame.new(origin)        -- bottom centre
		model:SetAttribute("Tier", mk.tier)
		model:PivotTo(CFrame.new())
		model.Parent = folder
		log(string.format("maker %-13s tier %d: %d meshes, %d collision parts", mk.name, mk.tier, n, #mk.collision))
	end
	import:Destroy()
end

local ok, rec = pcall(function() return CHS:TryBeginRecording("Fit military base") end)
local success, err = pcall(function()
	doBase()
	doMakers()
end)
if ok and rec then
	CHS:FinishRecording(rec, success and Enum.FinishRecordingOperation.Commit or Enum.FinishRecordingOperation.Cancel)
end
if not success then warn("[FIT] failed:", err) else log("done") end
